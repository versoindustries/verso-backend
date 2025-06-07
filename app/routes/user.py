from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
import app
import os
from app import db, mail, bcrypt  # Adjust 'app' to your actual app's name
from app.models import User
from app.forms import RegistrationForm, LoginForm, SettingsForm, EstimateRequestForm
from flask_mail import Message
from datetime import datetime, timedelta, date
import logging
from sqlalchemy import and_, cast, String

user = Blueprint('user', __name__)

@user.context_processor
def combined_context_processor():
    erf_form = EstimateRequestForm()
    return dict(erf_form=erf_form)

@user.route('/reset_password', methods=['POST'])
def reset_password():
    token = request.form.get('token')
    password = request.form.get('password')
    user = User.verify_reset_token(token)
    if user:
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('auth.login'))
    else:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('main.register'))

@user.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    settings_form = SettingsForm()

    if settings_form.validate_on_submit():
        current_user.email = settings_form.email.data
        current_user.bio = settings_form.bio.data
        current_user.location = settings_form.location.data

        if settings_form.password.data:
            current_user.set_password(settings_form.password.data)  # Assuming you have a set_password method

        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.settings'))

    elif request.method == 'GET':
        settings_form.email.data = current_user.email
        settings_form.bio.data = current_user.bio
        settings_form.location.data = current_user.location

    return render_template('settings.html', settings_form=settings_form)

@user.route('/dashboard')
@login_required
def dashboard():

    return render_template('UserDashboard/user_dashboard.html')


@user.route('/dashboard/commercial')
@login_required
def commercial_dashboard():
    if not current_user.has_role('commercial'):
        flash('Access denied. This area is for commercial users only.', 'danger')
        return redirect(url_for('user.dashboard'))


    return render_template(
        'UserDashboard/commercial_dashboard.html'
    )
