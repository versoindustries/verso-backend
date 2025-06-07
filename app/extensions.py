# app/extensions.py
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_mail import Mail
from flask_bcrypt import Bcrypt

login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()
bcrypt = Bcrypt()
