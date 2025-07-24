from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db, mail
from flask_mail import Message
from . import feedback_bp

@feedback_bp.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    if request.method == 'POST':
        rating = request.form.get('rating')
        feedback_text = request.form.get('feedback')
        
        # Send confirmation email
        try:
            msg = Message(
                "Your Feedback Has Been Received",
                sender="locusnoreply19@gmail.com",
                recipients=[current_user.email]
            )
            msg.body = f"""Thank you for your feedback!

Rating: {rating}/5
Feedback: {feedback_text}

We appreciate you taking the time to help us improve.
"""
            mail.send(msg)
            flash('Thank you for your feedback! A confirmation has been sent to your email.', 'success')
        except Exception as e:
            flash('Feedback submitted successfully, but we couldn\'t send the confirmation email.', 'warning')
        
        return redirect(url_for('dashboard.dashboard'))
    
    return render_template('feedback/feedback.html')
