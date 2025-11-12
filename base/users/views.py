from flask import Flask, Blueprint, render_template, request, session, redirect, url_for, flash, abort
from flask_login import login_user, login_required, logout_user, current_user
from base import db, registration_toggle
from datetime import datetime
from base.lumberjack.views import lumberjack_do
from base.models import User
from base.users.forms import RegistrationForm, LoginForm
from werkzeug.security import generate_password_hash, check_password_hash


users_blueprint = Blueprint('users', __name__, template_folder='templates/users')

@users_blueprint.route('/', methods=['GET'])
def users():
    #admin only
    return render_template('users.html')

@users_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    #env variable that allows me to toggle registration
    if registration_toggle == 'True':
        form = RegistrationForm()
        #force uname and email to lowercase
        #check if username or email exists
        if form.validate_on_submit():
            user = User(username=form.username.data,
                        email=form.email.data.lower(),
                        password=form.password.data)
            db.session.add(user)
            db.session.commit()
            lumberjack_do(datetime.utcnow(), current_user, "users", f"{ form.email.data } registered as {form.username.data}")
            flash('Thank you for registering. You can now login.')
            return redirect(url_for('users.login'))
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{ field } error: { error }", "danger")
        return render_template('register.html', form=form)
    else:
        abort(423)

@users_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # force submitted email to lowercase
        email = form.email.data.lower()
        user = db.session.execute(db.select(User).filter_by(email=email)).scalar()
        if User.check_email(email=email) and user.check_password(form.password.data) and user is not None:
            login_user(user)
            flash('You have been logged in.')
            lumberjack_do(datetime.utcnow(), current_user, "users", "User Logged In")
            next = request.args.get('next')
            if next == None or not next[0]=='/':
                next = url_for('users.welcome')
            return redirect(next)
        else:
            flash('Invalid username or password')
            return redirect(url_for('users.login'))
    return render_template('login.html', form=form)

@users_blueprint.route('/welcome', methods=['GET', 'POST'])
@login_required
def welcome():
    return render_template('welcome.html')

@users_blueprint.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    lumberjack_do(datetime.utcnow(), current_user, "users", "User Logged Out")
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))


# admin only -
# tie into an admin panel where I can manage users, reset pwds, ban, invite, toggle registration, etc
# Admin panel should link to admin functions in the other modules for managing logs and jobs (i.e. delete old to save space)

@users_blueprint.route("/user-by-id/<int:id>")
def user_by_id(id):
    user = db.get_or_404(User, id)
    return render_template("show_user.html", user=user)

@users_blueprint.route("/user-by-username/<username>")
def user_by_username(username):
    user = db.one_or_404(db.select(User).filter_by(username=username))
    return render_template("show_user.html", user=user)

@users_blueprint.route("/user-by-email/<email>")
def user_by_email(email):
    user = db.one_or_404(db.select(User).filter_by(email=email))
    return render_template("show_user.html", user=user)