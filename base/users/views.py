from flask import current_app, Flask, Blueprint, render_template, request, session, redirect, url_for, flash, abort
from flask_login import login_user, login_required, logout_user, current_user
from base import db
from base.decorators import admin_required
from datetime import datetime
from base.lumberjack.views import lumberjack_do
from base.models import User
from base.users.forms import RegistrationForm, LoginForm, BouncerList
from werkzeug.security import generate_password_hash, check_password_hash


users_blueprint = Blueprint('users', __name__, template_folder='templates/users')

@users_blueprint.route('/', methods=['GET'])
def users():
    #basic home for users
    #add account management functions
    return render_template('users-home.html')

@users_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    #env variable allows me to toggle registration OPEN CLOSED INVITE ONLY
    registration_mode = current_app.config['REGISTRATION_MODE']
    bouncer = False
    if registration_mode == "CLOSED":
        abort(423)
    elif registration_mode == "INVITE_ONLY":
        # bouncer tells the template to display a warning and checks if you're on the list
        bouncer = True
    form = RegistrationForm()
    if form.validate_on_submit():
        # check if email exists
        if User.check_email(email=form.email.data.lower()):
            flash('This Email is already registered.')
            lumberjack_do(datetime.utcnow(), current_user, "users",
                          f"Somebody tried to register as {form.email.data}")
            return redirect(url_for('users.register'))
        #check if the submitted email is on the approved list
        # if bouncer:

        # check if username exists
        elif User.check_username(username=form.username.data.lower()):
            flash('This username is already taken.')
            lumberjack_do(datetime.utcnow(), current_user, "users",
                          f"Somebody tried to register as {form.username.data}")
            return redirect(url_for('users.register'))

        else:
            user = User(username=form.username.data,
                        email=form.email.data.lower(),
                        password=form.password.data)
            # add registration date
            db.session.add(user)
            db.session.commit()
            lumberjack_do(datetime.utcnow(), current_user, "users",
                          f"{form.email.data} registered as {form.username.data}")
            flash('Thank you for registering. You can now login.')
            return redirect(url_for('users.login'))
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field} error: {error}", "danger")
    return render_template('users-register.html', form=form, bouncer=bouncer)



@users_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # force submitted email to lowercase
        email = form.email.data.lower()
        user = db.session.execute(db.select(User).filter_by(email=email)).scalar()
        #check if user is allowed to log in or if they're banned
        if User.check_email(email=email) and user.check_password(form.password.data) and user is not None:
            # here we are checking for ENV admins and updating the db
            if user.sync_admin_status():
                db.session.commit()
            #handling the login
            #update last login date
            login_user(user)
            flash('You have been logged in.')
            #logging the login
            lumberjack_do(datetime.utcnow(), current_user, "users", "User Logged In")
            #check if pwd reset is required and redirect to that page
            next = request.args.get('next')
            if next == None or not next[0]=='/':
                next = url_for('users.welcome')
            return redirect(next)
        else:
            flash('Invalid username or password')
            return redirect(url_for('users.login'))
    return render_template('users-login.html', form=form)

@users_blueprint.route('/welcome', methods=['GET', 'POST'])
@login_required
def welcome():
    return render_template('users-welcome.html')

@users_blueprint.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    lumberjack_do(datetime.utcnow(), current_user, "users", "User Logged Out")
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))


#reset pwd

#profile
#a page where users can see their past activity


#admin only

@users_blueprint.route('/lookup-users', methods=['GET', 'POST'])
@login_required
@admin_required
def lookup_users():
    #form submission for lookup
    # by id
        # if exists - opens manage user page

    # by email
        # if exists - opens manage user page

    # by username
        # if exists - opens manage user page

    #returns result as users and feeds to the same table as the GET

    #If not POST
    #lists all
    user_base = db.session.execute(db.select(User).order_by(User.email.desc())).scalars()
    users = [user.to_dict() for user in user_base]
    #add
    # registration date
    # last login date
    # banned
    # must reset pwd
    print(users)
    return render_template('users-lookup_users.html', users=users)


@users_blueprint.route('/invite-user', methods=['GET', 'POST'])
@login_required
@admin_required
def invite_user():
    #shows the bouncer's list
    #add/removes an email to a list of approved registrants

    pass

@users_blueprint.route('/manage-user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_user(user_id):
    user_data = db.session.execute(db.select(User).filter_by(id=user_id)).scalar()
    user = user_data.to_dict()
    #options:
    #ban
    #delete - removes user but allows re-register
    #reset pwd - creates a new pwd and requires a reset at next login
    #promote to admin
    #demote
    return render_template('users-user_detail.html', user=user)

@users_blueprint.route('/toggle-registration-mode', methods=['GET', 'POST'])
@login_required
@admin_required
def toggle_registration_mode():
    #updates the env variable for registration mode
    pass