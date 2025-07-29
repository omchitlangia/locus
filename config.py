# config.py
import os
from pathlib import Path

class Config:
    # Secret settings
    SECRET_KEY = 'your-hardcoded-fallback'
    SECURITY_PASSWORD_SALT = 'fallback-salt'

    # Database
    SQLALCHEMY_DATABASE_URI = (
        'mysql+pymysql://avnadmin:AVNS_RXM-NqbX7IPoOWx7mzY@locus-locus123.j.aivencloud.com:25327/logindata'
        '?ssl_ca=ca.pem'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'locusnoreply19@gmail.com'           # <-- change to your actual Gmail
    MAIL_PASSWORD = 'iqcwjhipozwbwatn'        # <-- Gmail app password
    MAIL_DEFAULT_SENDER = 'locusnoreply19@gmail.com'
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app','static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024


