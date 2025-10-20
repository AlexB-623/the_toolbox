from flask import Flask, Blueprint, render_template, request, session, redirect, url_for, flash, abort
from flask_login import login_user, login_required, logout_user
from base import db
from base.models import User
from base.users.forms import RegistrationForm, LoginForm
from werkzeug.security import generate_password_hash, check_password_hash


users_blueprint = Blueprint('users', __name__, template_folder='templates/users')

@users_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,
                    email=form.email.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Thank you for registering. You can now login.')
        return redirect(url_for('users.login'))
    return render_template('register.html', form=form)

@users_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user.check_password(form.password.data) and user is not None:
            login_user(user)
            flash('You have been logged in.')
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
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))