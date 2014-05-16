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

# Code and PDB downloads page.
app.add_url_rule('/code_and_PDB', 'code_and_PDB', view_func=views.code_and_PDB)

# Too many chains submitted error page
app.add_url_rule('/too_many_chains', 'too_many_chains', view_func=views.too_many_chains)

# Culling entry page.
app.add_url_rule('/culling', 'culling', view_func=views.culling, methods=['POST', 'GET'])

# Serve culled lists.
app.add_url_rule('/serve_list/<blobKey>', 'serve_list', view_func=views.serve_list)

# Results page.
app.add_url_rule('/results/<int:cullID>', 'results', view_func=views.results)
app.add_url_rule('/results_list/<int:cullID>/<nonredundant>', 'results_list', view_func=views.results_list)

# Admin culled list upload pages.
app.add_url_rule('/admin/cull_upload', 'cull_upload_form', view_func=views.cull_upload_form, methods=['POST', 'GET'])
app.add_url_rule('/admin/cull_upload/handler', 'cull_upload_handler', view_func=views.cull_upload_handler, methods=['POST', 'GET'])

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