from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user
from flask_mail import Message
from flask import current_app as app
# Assuming the below modules are part of your application
from app import db, mail, bcrypt  # Adjust 'yourapp' to your actual app's name
from app.models import User, Role  # Adjust 'yourapp.models' to your actual models' location
from app.forms import RegistrationForm, LoginForm, EstimateRequestForm  # Adjust 'yourapp.forms' to your actual forms' location

blog_blueprint = Blueprint('blog', __name__, template_folder='templates/')
news_update = Blueprint('news', __name__, template_folder='templates/')
updates_blueprint = Blueprint('updates', __name__, template_folder='templates')

@blog_blueprint.context_processor
def combined_context_processor():
    locations = get_locations()
    erf_form = EstimateRequestForm()
    return dict(erf_form=erf_form, hide_estimate_form=True)

@news_update.context_processor
def combined_context_processor():
    locations = get_locations()
    erf_form = EstimateRequestForm()
    return dict(erf_form=erf_form, hide_estimate_form=True)

@updates_blueprint.context_processor
def combined_context_processor():
    locations = get_locations()
    erf_form = EstimateRequestForm()
    return dict(erf_form=erf_form, hide_estimate_form=True)

@blog_blueprint.route('/blog')
def show_blog():
    return render_template('blog.html')

@blog_blueprint.route('/blog/blog1.html')
def custom_built_home_timeline():
    return render_template('blog1.html')
