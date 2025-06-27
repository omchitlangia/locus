from flask import Blueprint, render_template, redirect, request, url_for, session, flash
from app.extensions import db, bcrypt
from flask_login import current_user, login_user, login_required, logout_user, login_fresh  # Add this import
from app.models import User
from datetime import timedelta
from .email_utils import send_email, generate_token, confirm_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def home():
    return redirect('/welcome')

@auth_bp.route('/welcome')
def welcome():
    return render_template('/user_management/welcome.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm-password']

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('user_management/register.html')

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('user_management/register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('user_management/register.html')

        # Create user first
        try:
            hashed = bcrypt.generate_password_hash(password).decode('utf-8')
            user = User(username=username, email=email, password=hashed)
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'error')
            return render_template('user_management/register.html')

        # Now handle email separately
        try:
            token = generate_token(email)
            verify_url = url_for('auth.verify_email', token=token, _external=True)
            html = render_template('emails/verify_email.html', verify_url=verify_url)
            send_email(email, 'Verify Your Email - Locus', html)
            flash('Registration successful! Please check your email.', 'info')
            return redirect(url_for('auth.login'))
        except Exception as email_error:
            # User exists but email failed - notify them
            flash(f'Account created but verification email failed. Contact the support team.', 'warning')
            return redirect(url_for('auth.login'))

    return render_template('user_management/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already authenticated, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please enter both username and password', 'error')
            return redirect(url_for('auth.login'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            if not user.email_verified:
                flash('Please verify your email before logging in', 'warning')
                return redirect(url_for('auth.login'))
            
            # Simple login without force=True
            login_user(user)
            
            # Set session as modified
            session.modified = True
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('/user_management/login.html')

@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    # Debugging output
    print(f"Logging out user: {current_user.username}")
    
    # Clear Flask-Login session
    logout_user()
    
    # Clear Flask session completely
    session.clear()
    
    # Ensure session is marked as modified
    session.modified = True
    
    # Create a new empty session ID by generating a new one
    session['_new'] = True  # Forces new session ID generation
    
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('auth.login'))

# Add this route to handle session timeout
@auth_bp.route('/check-session')
def check_session():
    """Route to check if session is still valid"""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return {'logged_in': True, 'username': user.username}
    
    session.clear()
    return {'logged_in': False}

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    try:
        email = confirm_token(token)
    except:
        flash('Invalid or expired verification link.', 'error')
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Account not found.', 'error')
        return redirect(url_for('auth.register'))
    
    if user.email_verified:
        flash('Email already verified. Please login.', 'info')
    else:
        user.email_verified = True
        db.session.commit()
        flash('Email verified successfully!', 'success')
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_token(email)
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            html = render_template('emails/reset_password.html', reset_url=reset_url)
            send_email(email, 'Reset Your Password', html)
        
        flash('If an account exists, a reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('user_management/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = confirm_token(token)
    except:
        flash('Invalid or expired reset link.', 'error')
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Account not found.', 'error')
        return redirect(url_for('auth.register'))
    
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Password and Confirmed Password do not match!', 'error')
            return redirect(url_for('auth.login'))
        
        user.password = bcrypt.generate_password_hash(password).decode('utf-8')
        db.session.commit()
        flash('Password updated successfully!', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('user_management/reset_password.html', token=token)

@auth_bp.route('/resend-verification')
@login_required
def send_verification_again():
    user = User.query.get(session['user_id'])
    if user and not user.email_verified:
        token = generate_token(user.email)
        verify_url = url_for('auth.verify_email', token=token, _external=True)
        html = render_template('emails/verify_email.html', verify_url=verify_url)
        send_email(user.email, 'Verify Your Email - Locus', html)
        flash('Verification email resent!', 'info')
    else:
        flash('Your email is already verified.', 'info')
    return redirect(url_for('auth.dashboard'))

if __name__ == '__main__':
    auth_bp.run(debug=True)