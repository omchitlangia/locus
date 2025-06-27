# config.py

class Config:
    # Secret settings
    SECRET_KEY = 'your-hardcoded-fallback'
    SECURITY_PASSWORD_SALT = 'fallback-salt'

    # Database
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:locus123@localhost/loginData'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'locusnoreply19@gmail.com'           # <-- change to your actual Gmail
    MAIL_PASSWORD = 'iqcwjhipozwbwatn'        # <-- Gmail app password
    MAIL_DEFAULT_SENDER = 'locusnoreply19@gmail.com'
