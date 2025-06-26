from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from app.extensions import mail
from flask_mail import Message

def generate_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=current_app.config['SECURITY_PASSWORD_SALT'])

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.loads(token, salt=current_app.config['SECURITY_PASSWORD_SALT'], max_age=expiration)

def send_email(to, subject, html_body):
    print(f"Attempting to send email to: {to}")  # Debug output
    msg = Message(
        subject,
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[to],
        html=html_body
    )
    try:
        mail.send(msg)
        print("Email sent successfully")  # Debug output
    except Exception as e:
        print(f"Email send failed: {str(e)}")  # Debug output
        raise