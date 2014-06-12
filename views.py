from datetime import datetime
import os
import sys
import cgi

from main import app
import models

from google.appengine.api import mail
from google.appengine.ext import blobstore
from google.appengine.ext import deferred
from google.appengine.ext import ndb
from google.appengine.runtime import DeadlineExceededError

import logging

from flask import render_template, request, redirect, Response

import blob_deleter
import cull_worker
import download_generator
import leafcull

# Define some global variables needed by multiple pages.
MAXCHAINS = 500
CONTACTEMAIL = 'SimonCB765@gmail.com'
SENDEMAIL = False


def home():
    """Render the home page."""
    return render_template('home.html')

def code_and_PDB():
    """Render the page for downloading code and PDB data."""
    if request.method == 'POST':
        fileType = request.form['fileType']
        if fileType == 'Leaf':
            # The user wants to download the Leaf source code.
            fileForLocalCulling = models.LocalPDBFiles.get_by_id(fileType)
            blobKey = fileForLocalCulling.fileBlobKey
            blobInfo = blobstore.BlobInfo.get(blobKey)
            response = Response()
            response.headers['X-AppEngine-BlobKey'] = blobKey
            response.headers['Content-Disposition'] = 'attachment; filename={0}.tar'.format(fileType)
            return response
        elif fileType == 'PDB':
            # The user wants to download a subset of the PDB, so generate that subset.
            userInputChains = set([i.strip() for i in request.form['pastedInfo'].split('\n')])

            # Save the downloaded information.
            newPDBDownload = models.PDBDownload(finished=False)
            newPDBDownloadKey = newPDBDownload.put()
            newPDBDownloadID = newPDBDownloadKey.id()

            # Initiate the download asynchronously.
            deferred.defer(download_generator.main, newPDBDownloadID, userInputChains)

            return render_template('download_success.html', PDBDownloadID=newPDBDownloadID)
    elif request.method == 'GET':
        return render_template('code_and_PDB.html')

def download_results(PDBDownloadID):
    """Render the results of a PDB download request."""

    # Get the PDBDownload information.
    PDBDownload = models.PDBDownload.get_by_id(PDBDownloadID)
    finished = PDBDownload.finished

    # Determine the status of the download generation.
    if finished:
        # Generation finished successfully.
        status = 0
    else:
        # Generation hasn't finished.
        status = 1

    return render_template('download_results.html', PDBDownloadID=PDBDownloadID, status=status)

def too_many_chains():
    """Render the page indicating that too many chains were submitted."""
    return render_template('too_many_chains.html')

def contacts():
    """Render the contacts page."""
    return render_template('contacts.html')

def cull_upload_handler():
    """Process the information uploaded with the culled list."""
    similarity = request.form['maxIdentity']
    maxRes = request.form['maxRes']
    maxRVal = request.form['maxRVal']
    includeNonXray = 'N' if request.form['includeNonXray'] == 'no' else 'Y'
    includeAlphaCarbon = 'N' if request.form['includeAlphaCarbon'] == 'no' else 'Y'
    keyName = similarity + '_' + maxRes + '_' + maxRVal + '_' + includeNonXray + '_' + includeAlphaCarbon
    type, params = cgi.parse_header(request.files['culledListFile'].headers['Content-Type'])
    blobKey = blobstore.BlobKey(params['blob-key'])

    # Check if this upload will orphan a blob.
    existingEntity = models.PreCulledList.get_by_id(keyName)
    if existingEntity:
        existingKey = existingEntity.listBlobKey
        deferred.defer(blob_deleter.main, existingKey)

    newCulledList = models.PreCulledList(id=keyName, details=keyName, listBlobKey=blobKey)
    newCulledList.put()
    return 'List Uploaded<br>' + '<br>'.join(['Similarity - ' + similarity, 'MaxRes - ' + maxRes, 'MaxRVal - ' + maxRVal, 'NonXRay - ' + includeNonXray, 'Only Alpha Carbon - ' + includeAlphaCarbon])

def cull_upload_form():
    """Render the culled list upload page."""
    upload_url = blobstore.create_upload_url('/admin/cull_upload/handler')
    return render_template('cull_upload.html', upload_url=upload_url)

def local_PDB_upload_handler():
    """Process the information uploaded with the culled list."""
    keyName = request.form['fileType']
    type, params = cgi.parse_header(request.files['uploadedFile'].headers['Content-Type'])
    blobKey = blobstore.BlobKey(params['blob-key'])

    # Check if this upload will orphan a blob.
    existingEntity = models.LocalPDBFiles.get_by_id(keyName)
    if existingEntity:
        existingKey = existingEntity.fileBlobKey
        deferred.defer(blob_deleter.main, existingKey)

    uploadedFile = models.LocalPDBFiles(id=keyName, details=keyName, fileBlobKey=blobKey)
    uploadedFile.put()
    return 'Uploaded the {0} file'.format(keyName)

def local_PDB_upload_form():
    """Render the page to upload the chains and similarities."""
    upload_url = blobstore.create_upload_url('/admin/PDB_upload/handler')
    return render_template('local_PDB_upload.html', upload_url=upload_url)

def results_list(ID, file):
    """Serve up a file from a culling request"""

    if file == 'Cull_Input':
        # Get the CullJob information.
        cullJob = models.CullJob.get_by_id(ID)
        output = cullJob.chains
    elif file == 'Cull_NR':
        # Get the CullJob information.
        cullJob = models.CullJob.get_by_id(ID)
        output = cullJob.nonredundant
    elif file == 'PDB_Chains':
        # Get the PDB download information.
        PDBDownload = models.PDBDownload.get_by_id(ID)
        output = PDBDownload.chains
    elif file == 'PDB_Similarities':
        # Get the PDB download information.
        PDBDownload = models.PDBDownload.get_by_id(ID)
        output = PDBDownload.similarities

    return Response(output, mimetype='text/plain')

def results(cullID):
    """Display information about the status of the request."""

    # Get the CullJob information.
    cullJob = models.CullJob.get_by_id(cullID)
    finished = cullJob.finished
    startDate = cullJob.startDate

    # Determine the status of the culling.
    if finished:
        # Culling finished successfully.
        status = 0
    elif startDate:
        # Culling has started.
        timeDifference = datetime.utcnow() - startDate
        elapsed = divmod(timeDifference.days * 86400 + timeDifference.seconds, 60)
        if elapsed[0] > 11:
            # Culling timed out. Only ten minutes are allowed, but give some flexibility for differences in refreshing and reporting.
            status = 3
        else:
            # Culling underway still.
            status = 2
    else:
        # Culling hasn't started.
        status = 1

    return render_template('results.html', status=status, contactAddress=CONTACTEMAIL, cullID=cullID)

def help():
    """Render the help page."""
    return render_template('help.html')

def downloads():
    """Render the downloads page."""
    if request.method == 'POST':
        similarity = request.form['maxIdentity']
        maxRes = request.form['maxRes']
        maxRVal = request.form['maxRVal']
        includeNonXray = 'N' if request.form['includeNonXray'] == 'no' else 'Y'
        includeAlphaCarbon = 'N' if request.form['includeAlphaCarbon'] == 'no' else 'Y'
        keyName = similarity + '_' + maxRes + '_' + maxRVal + '_' + includeNonXray + '_' + includeAlphaCarbon
        culledList = models.PreCulledList.get_by_id(keyName)
        blobKey = culledList.listBlobKey
        blobInfo = blobstore.BlobInfo.get(blobKey)
        response = Response()
        response.headers['X-AppEngine-BlobKey'] = blobKey
        response.headers['Content-Disposition'] = 'attachment; filename=CulledProteins.gz'
        return response
    elif request.method == 'GET':
        return render_template('downloads.html')

def culling():
    """Render the culling entry page."""
    if request.method == 'POST':
        # Extract the user specified parameters.
        submittedChains = request.form['pastedInfo']
        sequenceIdentity = float(request.form['pc'])
        minRes = float(request.form['minRes'])
        maxRes = float(request.form['maxRes'])
        maxRVal = float(request.form['maxRVal'])
        enforceMinLength = request.form['enforceMinLength']
        minLen = -1 if not enforceMinLength == 'yes' else int(request.form['minLen'])
        enforceMaxLength = request.form['enforceMaxLength']
        maxLen = -1 if not enforceMaxLength == 'yes' else int(request.form['maxLen'])
        includeNonXray = True if request.form['includeNonXray'] == 'yes' else False
        includeAlphaCarbon = True if request.form['includeAlphaCarbon'] == 'yes' else False
        emailAddress = request.form['email']

        # Get the submitted chains.
        chainIdentifiers = set([i.strip() for i in submittedChains.split('\n')])  # The chains submitted by the user.

        # Establish the location of the data files containing the chain information.
        projectDirectory = os.path.dirname(os.path.realpath(__file__))
        chainData = os.path.join(projectDirectory, 'Data')
        chainData = os.path.join(chainData, 'Chains.tsv')

        # Determine the chains that meet the criteria supplied by the user. A chain is only accepted if its resolution is between the min and max
        # requested resolution, its r value is no greater than the requested maximum r value, its sequence length is within the requested seuence length
        # range (or no range was requested), it does not have a non-xray structure/non-xray structures are allowed and its structure does not only consist
        # of alpha carbons/alpha carbon only structures are being permitted.
        allValidChains = {}  # The chains that meet the user specified quality criteria.
        readChainData = open(chainData, 'r')
        readChainData.readline()  # Strip the header.
        for i in readChainData:
            # Parse the data file containing all the chains in the PDB, and record only those that meet the quality criteria.
            chunks = (i.strip()).split('\t')
            chain = chunks[0]
            resolution = float(chunks[1])
            rValue = float(chunks[2])
            sequenceLength = int(chunks[3])
            xRayNotUsed = chunks[4] == 'yes'
            alphaCarbonOnly = chunks[5] == 'yes'
            representativeGroup = chunks[6]
            invalid = ((chain not in chainIdentifiers) or
                       (xRayNotUsed and not includeNonXray) or
                       (resolution < minRes) or
                       (resolution > maxRes) or
                       (rValue > maxRVal) or
                       (alphaCarbonOnly and not includeAlphaCarbon) or
                       (minLen != -1 and sequenceLength < minLen) or
                       (maxLen != -1 and sequenceLength > maxLen)
                       )
            if not invalid:
                allValidChains[chain] = representativeGroup
        readChainData.close()

        # Determine the representative chains.
        representativeGroupings = {}
        for i in allValidChains:
            representativeGroupings[allValidChains[i]] = i

        # Determine whether culling should be started.
        numberUniqueChains = len(representativeGroupings)
        if numberUniqueChains == 0:
            # If no valid chains were submitted.
            return 'None of the chain identifiers that you submitted were recognised as valid chains. Please back up and try again.'
        elif numberUniqueChains > MAXCHAINS:
            # If too many chains were submitted.
            return render_template('too_many_chains.html', max=MAXCHAINS, received=numberUniqueChains)
        else:
            # Save the cull job.
            newCullJob = models.CullJob(similarity=sequenceIdentity, minRes=minRes, maxRes=maxRes, maxRVal=maxRVal, minLen=minLen, maxLen=maxLen,
                                        includeNonXray=includeNonXray, includeAlphaCarbon=includeAlphaCarbon, chains='\n'.join(chainIdentifiers),
                                        email=emailAddress, finished=False)
            newCullJobKey = newCullJob.put()
            newCullJobID = newCullJobKey.id()

            # Initiate the culling asynchronously.
            deferred.defer(cull_worker.main, newCullJobID, representativeGroupings, sequenceIdentity)

            # Send the notification emails if emails are being sent out.
            if SENDEMAIL:
                senderAddress = 'Leaf Results Notifier <Leaf.Notification@gmail.com>'
                subject = 'Leaf Protein Culling Results Notification'
                emailBody = ('Thanks for using the Leaf protein culling server. Your culling request has been successfully received, and is being processed now. ' +
                             'The results of your request can be found here: {0}.'.format('ResLoc'))
                mail.send_mail(senderAddress, emailAddress, subject, emailBody)

            # Put up the successful submission page.
            return render_template('culling_success.html', sequenceIdentity=sequenceIdentity, minRes=minRes, maxRes=maxRes, maxRVal=maxRVal,
                                   minLen='Not Enforced' if minLen == -1 else minLen, maxLen='Not Enforced' if maxLen == -1 else maxLen,
                                   includeNonXray='Yes' if includeNonXray else 'No', includeAlphaCarbon='Yes' if includeAlphaCarbon else 'No',
                                   email=emailAddress if SENDEMAIL else False, cullJobID=newCullJobID)
    elif request.method == 'GET':
        return render_template('culling.html', maxChains=MAXCHAINS)