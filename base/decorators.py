from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def admin_function(*args, **kwargs):
        if current_user.has_admin_access():
            return f(*args, **kwargs)
        else:
            abort(403)

    admin_function._admin_required = True
    return admin_function
