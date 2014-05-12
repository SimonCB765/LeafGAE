import os
import sys
import cgi

from main import app
import models

from google.appengine.ext import blobstore

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
                                    minLen=-1 if not minLen else int(minLen), maxLen=-1 if not maxLen else int(maxLen), includeNonXray=includeNonXray,
                                    includeAlphaCarbon=includeAlphaCarbon, chains='\n'.join(chunkedChains), email=emailAddress)
        newCullJobKey = newCullJob.put()
        newCullJobID = newCullJobKey.id()
		
		# Start up the culling asynchronously.
        
        # Put up the successful submission page.
        return render_template('culling_success.html', sequenceIdentity=sequenceIdentity, minRes=minRes, maxRes=maxRes, maxRVal=maxRVal,
                               minLen=minLen or 'Not Enforced', maxLen=maxLen or 'Not Enforced', includeNonXray='Yes' if includeNonXray else 'No',
                               includeAlphaCarbon='Yes' if includeAlphaCarbon else 'No', email=emailAddress)
    elif request.method == 'GET':
        return render_template('culling.html')