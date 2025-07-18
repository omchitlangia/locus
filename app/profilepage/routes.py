from flask import render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models import User
from . import profile_bp
from app.business_health.routes import ALL_KPIS, calculate_automatic_kpis
import os
from werkzeug.utils import secure_filename
from config import Config

@profile_bp.route('/profile')
@login_required
def profile():
    try:
        # Initialize all KPIs with None
        kpis = {k: None for category in ALL_KPIS.values() for k in category}
        
        # Calculate automatic KPIs from database
        auto_kpis = calculate_automatic_kpis(current_user.id)
        kpis.update(auto_kpis)

        # Calculate health score using only available KPIs
        valid_kpis = {k: v for k, v in kpis.items() if v is not None and v >= 0}
        health_score = min(
            sum(valid_kpis.values()) / len(valid_kpis) if valid_kpis else 0,
            100
        )
        
        return render_template('/profilepage/profile.html', 
                            user=current_user,
                            health_score=round(health_score, 2),
                            kpis=kpis)

    except Exception as e:
        current_app.logger.error(f"Profile page error: {str(e)}", exc_info=True)
        return render_template('/profilepage/profile.html',
                            user=current_user,
                            health_score=0,
                            kpis={k: None for category in ALL_KPIS.values() for k in category})

@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        try:
            # Update basic info
            current_user.username = request.form.get('username', current_user.username)
            current_user.email = request.form.get('email', current_user.email)
            
            # Update business info
            current_user.business_name = request.form.get('business_name', '')
            current_user.business_type = request.form.get('business_type', '')
            current_user.industry = request.form.get('industry', '')
            current_user.location = request.form.get('location', '')
            
            # Handle profile picture upload
            if 'profile_pic' in request.files:
                file = request.files['profile_pic']
                if file.filename != '' and allowed_file(file.filename):
                    # Delete old file if exists
                    if current_user.profile_pic:
                        try:
                            old_file = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.profile_pic)
                            if os.path.exists(old_file):
                                os.remove(old_file)
                        except Exception as e:
                            current_app.logger.error(f"Error deleting old profile pic: {str(e)}")
                    
                    # Save new file
                    filename = secure_filename(f"user_{current_user.id}_{file.filename}")
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    current_user.profile_pic = filename
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile.profile'))
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Profile update error: {str(e)}", exc_info=True)
            flash(f'Error updating profile: {str(e)}', 'error')
    
    return render_template('/profilepage/edit_profile.html', user=current_user)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']