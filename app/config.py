import os

class Config:
    WTF_CSRF_ENABLED = True
    
    # Use Heroku's DATABASE_URL if available (production), fallback to SQLite for local development
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', "sqlite:///mydatabase.sqlite").replace('postgres://', 'postgresql://')

    SQLALCHEMY_TRACK_MODIFICATIONS = False