from flask import render_template, request, redirect, url_for
from flask_login import login_required, current_user
from . import checklist_bp
from app import db
from app.models import StartupChecklist
from flask import flash

# Define the checklist items
CHECKLIST_ITEMS = {
    'gst': 'Register for GST',
    'domain': 'Buy your domain name',
    'branding': 'Create a brand kit (logo, font, colors)',
    'bank': 'Open a business bank account',
    'team': 'Hire your first team member',
    'website': 'Launch a landing page',
    'socials': 'Create startup social media profiles'
}

@checklist_bp.route('/checklist', methods=['GET', 'POST'])
@login_required
def checklist():
    # On POST: update checklist items
    if request.method == 'POST':
        for key in CHECKLIST_ITEMS:
            item = StartupChecklist.query.filter_by(user_id=current_user.id, item_key=key).first()
            if not item:
                item = StartupChecklist(user_id=current_user.id, item_key=key)
            item.completed = (key in request.form)
            db.session.add(item)
        db.session.commit()
        # Inside POST block
        flash("Checklist progress saved successfully!", "success")
        return redirect(url_for('checklist.checklist'))

    # On GET: load saved progress
    progress = {key: False for key in CHECKLIST_ITEMS}
    user_items = StartupChecklist.query.filter_by(user_id=current_user.id).all()
    for item in user_items:
        progress[item.item_key] = item.completed

    return render_template('checklist/checklist.html', items=CHECKLIST_ITEMS, progress=progress)
