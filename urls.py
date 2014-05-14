from main import app
import views

from flask import render_template


# Home page.
app.add_url_rule('/', 'home', view_func=views.home)

# Contact page.
app.add_url_rule('/contacts', 'contacts', view_func=views.contacts)

# Help page.
app.add_url_rule('/help', 'help', view_func=views.help)

# Downloads page.
app.add_url_rule('/downloads', 'downloads', view_func=views.downloads, methods=['POST', 'GET'])

# Culling entry page.
app.add_url_rule('/culling', 'culling', view_func=views.culling, methods=['POST', 'GET'])

# Serve culled lists.
app.add_url_rule('/serve_list/<blobKey>', 'serve_list', view_func=views.serve_list)

# Serve lists of plaintext chains.
app.add_url_rule('/display_chains/<cullID>/<nonredundant>', 'display_chains', view_func=views.display_chains)

# Task Queue URL for performing culling.
app.add_url_rule('/admin/cull_worker', 'cull_worker', view_func=views.cull_worker, methods=['POST'])

# Admin culled list upload pages.
app.add_url_rule('/admin/cull_upload', 'cull_upload_form', view_func=views.cull_upload_form, methods=['POST', 'GET'])
app.add_url_rule('/admin/cull_upload/handler', 'cull_upload_handler', view_func=views.cull_upload_handler, methods=['POST', 'GET'])


#    url(r'^cullingchoice/$', 'Leaf.views.cullingchoice'),
#    url(r'^user_culling/$', 'Leaf.views.user_culling'),
#    url(r'^user_pdb_culling/$', 'Leaf.views.user_pdb_culling'),
#    url(r'^whole_pdb_culling/$', 'Leaf.views.whole_pdb_culling'),
#    url(r'^culling/user_submit/$', 'Leaf.views.user_submit'),
#    url(r'^culling/user_pdb_submit/$', 'Leaf.views.user_pdb_submit'),
##    url(r'^culling/whole_pdb_submit/$', 'Leaf.views.whole_pdb_submit'),
#    url(r'^downloads/(?P<fileName>[0-9a-zA-Z_./]+)/$', 'Leaf.views.download_gzipped'),
##    url(r'^requestsent/$', 'Leaf.views.sent'),
#    url(r'^requestsent/(?P<result_id>\d+)/(?P<cullType>[a-z]+)/$', 'Leaf.views.sent'),
##    url(r'^results/[0-9]+/[0-9]+/[0-9]+/(?P<result_id>\d+)/(?P<cullType>[a-z]+)/$', 'Leaf.views.results'),
#    url(r'^results/[0-9]+/[0-9]+/[0-9]+/(?P<result_id>\d+)/(?P<cullType>[a-z]+)/(?P<fileName>[a-zA-Z_]+)/$', 'Leaf.views.txtlist')

###################
# Error handlers. #
###################
# Handle 404 errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Handle 500 errors
@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500