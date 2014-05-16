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
    return render_template('code_and_PDB.html')

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
    newCulledList = models.PreCulledList(id=keyName, details=keyName, listBlobKey=blobKey)
    newCulledList.put()
    return 'List Uploaded<br>' + '<br>'.join(['Similarity - ' + similarity, 'MaxRes - ' + maxRes, 'MaxRVal - ' + maxRVal, 'NonXRay - ' + includeNonXray, 'Only Alpha Carbon - ' + includeAlphaCarbon])

def cull_upload_form():
    """Render the culled list upload page."""
    upload_url = blobstore.create_upload_url('/admin/cull_upload/handler')
    return render_template('cull_upload.html', upload_url=upload_url)

def serve_list(blobKey):
    """Serve a culled list."""
    blobInfo = blobstore.BlobInfo.get(blobKey)
    response = Response()
    response.headers['X-AppEngine-BlobKey'] = blobKey
    response.headers['Content-Disposition'] = 'attachment; filename=CulledProteins'
    return response

def results_list(cullID, nonredundant):
    """Serve up a file from a culling request"""

    # Get the CullJob information.
    cullJob = models.CullJob.get_by_id(cullID)
    chains = cullJob.nonredundant if nonredundant == 'NR' else cullJob.chains

    return Response(chains, mimetype='text/plain')

def results(cullID):
    """Display information about the status of the request."""

    # Get the CullJob information.
    cullJob = models.CullJob.get_by_id(cullID)
    chains = cullJob.chains
    nonredundantChains = cullJob.nonredundant
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
        return redirect('/serve_list/' + str(blobKey))
    elif request.method == 'GET':
        return render_template('downloads.html')

def culling():
    """Render the culling entry page."""
    if request.method == 'POST':
        # Extract the user specified parameters.
        submittedChains = request.form['pastedInfo']
        sequenceIdentity = request.form['pc']
        minRes = request.form['minRes']
        maxRes = request.form['maxRes']
        maxRVal = request.form['maxRVal']
        enforceMinLength = request.form['enforceMinLength']
        minLen = None
        if enforceMinLength == 'yes':
            minLen = request.form['minLen']
        enforceMaxLength = request.form['enforceMaxLength']
        maxLen = None
        if enforceMaxLength == 'yes':
            maxLen = request.form['maxLen']
        includeNonXray = True if request.form['includeNonXray'] == 'yes' else False
        includeAlphaCarbon = True if request.form['includeAlphaCarbon'] == 'yes' else False
        emailAddress = request.form['email']

        # Process the chains.
        chunkedChains = set([i.strip() for i in submittedChains.split('\n')])
        chainKeyNames = list(chunkedChains)  # The chains submitted by the user.
        chainEntities = ndb.get_multi([ndb.Key('Chain', i) for i in chainKeyNames])  # The chain entities of the submitted chains.

        # Determine whether culling should be started.
        numberUniqueChains = len(set([i.representativeChainGrouping for i in chainEntities]))
        if not chainEntities[0]:
            # If no valid chains were submitted.
            return 'No valid chains were submitted. Please back up and try again.'
        elif numberUniqueChains > MAXCHAINS:
            # If too many chains were submitted.
            return render_template('too_many_chains.html', max=MAXCHAINS, received=numberUniqueChains)
        else:
            # Save the cull job.
            newCullJob = models.CullJob(similarity=float(sequenceIdentity), minRes=float(minRes), maxRes=float(maxRes), maxRVal=float(maxRVal),
                                        minLen=0 if not minLen else int(minLen), maxLen=0 if not maxLen else int(maxLen), includeNonXray=includeNonXray,
                                        includeAlphaCarbon=includeAlphaCarbon, chains='\n'.join(chunkedChains), email=emailAddress, finished=False)
            newCullJobKey = newCullJob.put()
            newCullJobID = newCullJobKey.id()

            # Initiate the culling asynchronously.
            deferred.defer(cull_worker, newCullJobID, chainEntities)

            # Send the notification emails if emails are being sent out.
            if SENDEMAIL:
                senderAddress = 'Leaf Results Notifier <Leaf.Notification@gmail.com>'
                subject = 'Leaf Protein Culling Results Notification'
                emailBody = ('Thanks for using the Leaf protein culling server. Your culling request has been successfully received, and is being processed now. ' +
                             'The results of your request can be found here: {0}.'.format('ResLoc'))
                mail.send_mail(senderAddress, emailAddress, subject, emailBody)

            # Put up the successful submission page.
            return render_template('culling_success.html', sequenceIdentity=sequenceIdentity, minRes=minRes, maxRes=maxRes, maxRVal=maxRVal,
                                   minLen=minLen or 'Not Enforced', maxLen=maxLen or 'Not Enforced', includeNonXray='Yes' if includeNonXray else 'No',
                                   includeAlphaCarbon='Yes' if includeAlphaCarbon else 'No', email=emailAddress if SENDEMAIL else False,
                                   cullJobID=newCullJobID)
    elif request.method == 'GET':
        return render_template('culling.html', maxChains=MAXCHAINS)

def cull_worker(cullJobID, chainEntities):
    """Perform the culling."""

    # Setup logging for exceptions.
    logging.getLogger().setLevel(logging.DEBUG)

    # Initialise notification variables for access in the except statements.
    goodChainEntities = []
    similarityGroups = []
    numberSimmilarities = 0

    try:
        # Get the user request data.
        cullJob = models.CullJob.get_by_id(cullJobID)  # The CullJob entity.
        requestedSimilarity = cullJob.similarity
        requestedMinRes = cullJob.minRes
        requestedMaxRes = cullJob.maxRes
        requestedMaxRVal = cullJob.maxRVal
        requestedMinLen = cullJob.minLen
        requestedMaxLen = cullJob.maxLen
        requestedIncludeNonXRay = cullJob.includeNonXray
        requestedIncludeAlphaCarbon = cullJob.includeAlphaCarbon
        userEmail = cullJob.email

        # Record that the culling has started.
        cullJob.startDate = datetime.utcnow()

        # Determine the entries that meet the criteria supplied by the user. A chain is only accepted if its resolution is between the min and max
        # requested resolution, its r value is no greater than the requested maximum r value, its sequence length is within the requested seuence length
        # range (or no range was requested), it does not have a non-xray structure/non-xray structures are allowed and its structure does not only consist
        # of alpha carbons/alpha carbon only structures are being permitted.
        goodChainEntities = [i for i in chainEntities if (i.resolution >= requestedMinRes) and (i.resolution <= requestedMaxRes) and
                             (i.rVal <= requestedMaxRVal) and (i.sequenceLength >= requestedMinLen) and
                             (i.sequenceLength <= requestedMaxLen or requestedMaxLen == 0) and (i.nonXRay <= requestedIncludeNonXRay) and
                             (i.alphaCarbonOnly <= requestedIncludeAlphaCarbon)]

        # Determine the unique similarity groups of the chains that meet the criteria.
        similarityGroups = [i.representativeChainGrouping for i in goodChainEntities]  # The similarity groups of the submitted chains.
        uniqueGroups = dict((i[0], i[1].chain) for i in zip(similarityGroups, goodChainEntities))  # Mapping of each unique similarity group (key) to its
                                                                                                   # representative chain (value).
        similarityGroups = uniqueGroups.keys()  # Unique similarity groups.

        # Setup the query for extracting the similarities for the unique similarity group.
        similarityQuery = models.Similarity.query()
        similarityQuery = similarityQuery.filter(models.Similarity.chainGroupingA.IN(similarityGroups))
        similarityQuery = similarityQuery.filter(models.Similarity.chainGroupingB.IN(similarityGroups))
        similarityQuery = similarityQuery.filter(models.Similarity.similarity >= requestedSimilarity)

        # Determine similarities between similarity groups.
        similarities = dict((uniqueGroups[i], set([])) for i in similarityGroups)
        for i in similarityQuery:
            chainA = uniqueGroups[i.chainGroupingA]
            chainB = uniqueGroups[i.chainGroupingB]
            similarities[chainA].add(chainB)
            similarities[chainB].add(chainA)
            numberSimmilarities += 1
        numberSimmilarities = str(numberSimmilarities) + ' (total)'

        # Perform culling.
        removedChains = leafcull.main(similarities)

        # Record the results.
        cullJob.nonredundant = '\n'.join([uniqueGroups[i] for i in similarityGroups if not uniqueGroups[i] in removedChains])
        cullJob.finished = True
        cullJob.put()
    except:
        logging.exception('CullJob {0} broke down. It contained {1} good chains, {2} uniqe chains and {3) similarities.'.format(cullJobID,
                          len(goodChainEntities), len(similarityGroups), numberSimmilarities))

    return ''