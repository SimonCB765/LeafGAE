import os
import sys
import cgi

from main import app
import models

from google.appengine.api import taskqueue
from google.appengine.ext import blobstore
from google.appengine.ext import ndb

from flask import render_template, request, redirect, Response, flash


def home():
    """Render the home page."""
    return render_template('home.html')

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

def display_chains(cullID, nonredundant):
    """Serve a plaintext list of chains."""
    cullJob = models.CullJob.get_by_id(cullID)
    chains = cullJob.nonredundant if nonredundant == 'NR' else cullJob.chains
    #response.headers['Content-Type'] = 'text/plain'
    return Response(chains, mimetype='text/plain')

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
        if enforceMinLength == 'yes':
            maxLen = request.form['maxLen']
        includeNonXray = True if request.form['includeNonXray'] == 'yes' else False
        includeAlphaCarbon = True if request.form['includeAlphaCarbon'] == 'yes' else False
        emailAddress = request.form['email']

        # Process the chains.
        chunkedChains = [i.strip() for i in submittedChains.split('\n')]

        # Save the cull job.
        newCullJob = models.CullJob(similarity=float(sequenceIdentity), minRes=float(minRes), maxRes=float(maxRes), maxRVal=float(maxRVal),
                                    minLen=0 if not minLen else int(minLen), maxLen=0 if not maxLen else int(maxLen), includeNonXray=includeNonXray,
                                    includeAlphaCarbon=includeAlphaCarbon, chains='\n'.join(chunkedChains), email=emailAddress)
        newCullJobKey = newCullJob.put()
        newCullJobID = newCullJobKey.id()

        # Initiate the culling asynchronously.
        taskqueue.add(url='/admin/cull_worker', params={'id' : newCullJobID})

        # Put up the successful submission page.
        return render_template('culling_success.html', sequenceIdentity=sequenceIdentity, minRes=minRes, maxRes=maxRes, maxRVal=maxRVal,
                               minLen=minLen or 'Not Enforced', maxLen=maxLen or 'Not Enforced', includeNonXray='Yes' if includeNonXray else 'No',
                               includeAlphaCarbon='Yes' if includeAlphaCarbon else 'No', email=emailAddress)
    elif request.method == 'GET':
        return render_template('culling.html')

def cull_worker():
    """Perform the culling."""

    # Get the user request data.
    cullJobID = int(request.form['id'])  # The ID of the CullJob request.
    cullJob = models.CullJob.get_by_id(cullJobID)  # The CullJob entity.
    requestedSimilarity = cullJob.similarity
    requestedMinRes = cullJob.minRes
    requestedMaxRes = cullJob.maxRes
    requestedMaxRVal = cullJob.maxRVal
    requestedMinLen = cullJob.minLen
    requestedMaxLen = cullJob.maxLen
    requestedIncludeNonXRay = cullJob.includeNonXray
    requestedIncludeAlphaCarbon = cullJob.includeAlphaCarbon
    chainKeyNames = list(set([i.strip() for i in (cullJob.chains).split('\n')]))  # The chains submitted by the user.
    chainEntities = ndb.get_multi([ndb.Key('Chain', i) for i in chainKeyNames])  # The chain entities of the submitted chains.

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

    # Extract the similarities for the unique similarity group.
    similarityQuery = models.Similarity.query()
    similarityQuery = similarityQuery.filter(models.Similarity.chainGroupingA.IN(similarityGroups))
    similarityQuery = similarityQuery.filter(models.Similarity.chainGroupingB.IN(similarityGroups))
    similarityQuery = similarityQuery.filter(models.Similarity.similarity >= requestedSimilarity)
    similarities = [[], []]
    for i in similarityQuery:
        similarities[0].append(uniqueGroups[i.chainGroupingA])
        similarities[1].append(uniqueGroups[i.chainGroupingB])

    # Record the chains that are too similar.
    cullJob.similarities = '\n'.join([i + '\t' + j for i, j in zip(similarities[0], similarities[1])])
    cullJob.put()

    # Record the results.
    cullJob.nonredundant = str(uniqueGroups)
    cullJob.put()
    return ''