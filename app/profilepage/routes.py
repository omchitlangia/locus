from flask import render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models import User
from . import profile_bp

import os
from werkzeug.utils import secure_filename
import time

# Allowed image extensions for profile pictures
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config.get('ALLOWED_EXTENSIONS', {'png','jpg','jpeg','gif'})

@profile_bp.route('/profile')
@login_required
def profile():
    try:
        # Fetch health_score directly from DB - no recalculation here!
        health_score = current_user.health_score or 0

        # Optional: If you want to display KPIs already stored or accessible here, you can add
        # For now, pass empty dict (or fetch if you have stored KPIs)
        kpis = {}

        return render_template(
            '/profilepage/profile.html',
            user=current_user,
            health_score=round(health_score, 2),
            kpis=kpis
        )
    except Exception as e:
        current_app.logger.error(f"Profile page error: {str(e)}", exc_info=True)
        return render_template(
            '/profilepage/profile.html',
            user=current_user,
            health_score=0,
            kpis={}
        )


@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        try:
            # Update basic user info safely
            current_user.username = request.form.get('username', current_user.username)
            current_user.email = request.form.get('email', current_user.email)

            # Update business info fields, default to empty string if missing
            current_user.business_name = request.form.get('business_name', '')
            current_user.business_type = request.form.get('business_type', '')
            current_user.industry = request.form.get('industry', '')
            current_user.location = request.form.get('location', '')

            # Handle profile picture upload if present
            if 'profile_pic' in request.files:
                file = request.files['profile_pic']

                if file and file.filename != '' and allowed_file(file.filename):
                    upload_path = os.path.join(current_app.root_path, 'static', 'uploads')
                    os.makedirs(upload_path, exist_ok=True)

                    # Remove old profile pic if present
                    if current_user.profile_pic:
                        try:
                            old_file_path = os.path.join(upload_path, current_user.profile_pic)
                            if os.path.exists(old_file_path):
                                os.remove(old_file_path)
                        except Exception as e:
                            current_app.logger.error(f"Error deleting old profile pic: {str(e)}")

                    # Save new profile pic with secure filename
                    ext = os.path.splitext(file.filename)[1].lower()
                    filename = f"user_{current_user.id}_{int(time.time())}{ext}"
                    filepath = os.path.join(upload_path, filename)
                    file.save(filepath)

                    # Update user's profile_pic filename in DB
                    current_user.profile_pic = filename

            # Commit all changes to DB
            db.session.commit()

            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile.profile'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Profile update error: {str(e)}", exc_info=True)
            flash(f'Error updating profile: {str(e)}', 'error')
            return render_template('/profilepage/edit_profile.html', user=current_user)
    else:
        # GET request just shows the edit profile form with current user data
        return render_template('/profilepage/edit_profile.html', user=current_user)
