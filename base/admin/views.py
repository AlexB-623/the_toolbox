from flask import current_app, Flask, Blueprint, render_template, request, session, redirect, url_for, flash, abort
from flask_login import login_user, login_required, logout_user, current_user
from base import db, registration_toggle
from base.decorators import admin_required
from datetime import datetime
from base.lumberjack.views import lumberjack_do
from base.models import User

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
@admin_required
def admin():
    # directory of admin functions
    admin_routes = get_admin_routes()
    #list is very basic, I can make this prettier and easier to navigate
    routes = [route['endpoint'] for route in admin_routes]
    return render_template('admin-home.html', routes=routes)
