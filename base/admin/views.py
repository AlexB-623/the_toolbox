from flask import current_app, Blueprint, render_template
from flask_login import login_required

from os import getcwd
import markdown

cwd = getcwd()

admin_blueprint = Blueprint('admin', __name__, template_folder='templates/admin')

def get_admin_routes():
    routes = []
    for rule in current_app.url_map.iter_rules():
        endpoint = rule.endpoint
        view_func = current_app.view_functions.get(endpoint)

        if getattr(view_func, "_admin_required", False):
            routes.append({
                "rule": rule.rule,
                "endpoint": endpoint,
                "methods": sorted(rule.methods - {"HEAD", "OPTIONS"})
            })
    return routes


@admin_blueprint.route('/')
@login_required
def admin():
    # directory of admin functions
    # Needs an about section
    with open (f'{cwd}/admin/data/about.txt', 'r') as f:
        md_about = f.read()
        f.close()
        about = markdown.markdown(md_about)
    admin_routes = get_admin_routes()
    #list is very basic, I can make this prettier and easier to navigate
    routes = [route['endpoint'] for route in admin_routes]
    return render_template('admin-home.html', routes=routes, about=about)
