from flask import render_template, request, redirect, url_for
from . import quiz_bp
from .logic import calculate_result, descriptions

QUESTIONS = [
    {
        "question": "Investors just backed out hours before launch. What’s your gut move?",
        "options": {
            "A": "Update projections and craft a fallback plan",
            "B": "Post a raw LinkedIn update about the setback",
            "C": "Launch anyway — users > investors",
            "D": "DM your user community for ideas and support"
        }
    },
    {
        "question": "Your app goes viral overnight. What's your first instinct?",
        "options": {
            "A": "Scale infra and monitor performance",
            "B": "Screenshot every mention and tweet a thread",
            "C": "Drop a follow-up feature while hype is hot",
            "D": "Email your earliest users to thank them"
        }
    },
    {
        "question": "You’re at a pitch event with tech giants. How do you stand out?",
        "options": {
            "A": "Show your churn rate drop over 6 months",
            "B": "Tell a story about the first person you helped",
            "C": "Drop an outrageous stat — then back it up",
            "D": "Say “We’re not competing — we’re collaborating”"
        }
    },
    {
        "question": "You just got negative feedback on your UI. What’s your response?",
        "options": {
            "A": "Pull heatmaps and session replays",
            "B": "Ask if they’d like to co-design the fix",
            "C": "Ship a redesign by the weekend",
            "D": "Respond kindly and log it for team review"
        }
    },
    {
        "question": "It’s 3 AM and you’re still working. Why?",
        "options": {
            "A": "You’re AB testing a new CTA button",
            "B": "You’re building a “thank you” feature for loyal users",
            "C": "You want to wake up to something you just shipped",
            "D": "You’re crafting a Notion doc titled “What We’ve Learned”"
        }
    },
    {
        "question": "You notice your top competitor just copied your feature. You…",
        "options": {
            "A": "Benchmark and adapt — you’ll stay ahead",
            "B": "Tweet “we see you 👀” with a wink",
            "C": "Launch your next big idea first",
            "D": "Ask users what they like/don’t like about both"
        }
    },
    {
        "question": "Your team is stuck deciding what to build next. What’s your role?",
        "options": {
            "A": "You run a survey and share insights",
            "B": "You ask: “What excites us most?”",
            "C": "You say “Let’s just test it” and assign work",
            "D": "You create a Miro board and open the floor"
        }
    }
]

@quiz_bp.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        answers = [request.form.get(f'q{i+1}') for i in range(7)]
        if None in answers:
            return render_template('quiz.html', questions=QUESTIONS, error="Please answer all questions.")
        persona = calculate_result(answers)
        return redirect(url_for('quiz.result', persona=persona))
    return render_template('quiz/quiz.html', questions=QUESTIONS)

@quiz_bp.route('/quiz/result/<persona>')
def result(persona):
    data = descriptions.get(persona)
    return render_template('quiz/result.html', persona=persona, data=data)
