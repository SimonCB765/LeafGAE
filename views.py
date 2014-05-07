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
    flash('WARNING: Some parameters have invalid values. The fields with invalid values are highlighted in orange. Please correct the highlighted fields before submitting.')
    return render_template('culling.html', pc=20, minRes=0.0, maxRes=3.0, maxRVal=0.5, minLen=40, maxLen=10000, enforceMinLength=False,
        enforceMaxLength=False, includeNonXray=False, includeAlphaCarbon=False)