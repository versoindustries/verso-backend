from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app import Config, create_app, db

app = create_app()

# db.init_app(app)  # This line is not necessary if db has been initialized in create_app

with app.app_context():
    #db.drop_all()
    db.create_all()
