from flask import Blueprint

quiz_bp = Blueprint('quiz', __name__)

from . import routes

# Register the filter globally when blueprint is initialized
@quiz_bp.app_template_filter('question_text')
def question_text(index):
    QUESTIONS = [
        "Investors just backed out hours before launch. What’s your gut move?",
        "Your app goes viral overnight. What's your first instinct?",
        "You’re at a pitch event with tech giants. How do you stand out?",
        "You just got negative feedback on your UI. What’s your response?",
        "It’s 3 AM and you’re still working. Why?",
        "You notice your top competitor just copied your feature. You…",
        "Your team is stuck deciding what to build next. What’s your role?"
    ]
    return QUESTIONS[index]
