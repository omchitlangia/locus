personas = {
    'A': 'Data Disciple',
    'B': 'Story Seller',
    'C': 'Hustle Hacker',
    'D': 'Empathy Operator'
}

descriptions = {
    'Data Disciple': {
        'emoji': '📊',
        'desc': 'Logic-led, spreadsheet-brained, and obsessed with KPIs.',
        'tips': 'Automate what you can. Avoid analysis paralysis.'
    },
    'Story Seller': {
        'emoji': '🎤',
        'desc': 'You inspire and lead with vision and narrative.',
        'tips': 'Back emotion with evidence. Story + substance wins.'
    },
    'Hustle Hacker': {
        'emoji': '⚡',
        'desc': 'Bold, fast-moving, MVP-loving builder.',
        'tips': 'Ship fast, but pause to reflect.'
    },
    'Empathy Operator': {
        'emoji': '💞',
        'desc': 'Team-focused and user-first in every decision.',
        'tips': 'Lead with care, but guard your time.'
    }
}

def calculate_result(answers):
    score = {'Data Disciple': 0, 'Story Seller': 0, 'Hustle Hacker': 0, 'Empathy Operator': 0}
    mapping = {'A': 'Data Disciple', 'B': 'Story Seller', 'C': 'Hustle Hacker', 'D': 'Empathy Operator'}
    for ans in answers:
        score[mapping[ans]] += 1
    return max(score, key=score.get)
