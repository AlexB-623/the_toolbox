from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def admin_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)  # Unauthorized
        if not current_user.has_admin_access:
            abort(403)  # Forbidden
        return f(*args, **kwargs)

    admin_function._admin_required = True
    return admin_function
