from flask import Blueprint, jsonify, request, session
from model.models import Feedback
from model.db import db

feedback_bp = Blueprint('feedback', __name__)

@feedback_bp.route('/api/feedback', methods=['POST'])
def save_feedback():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    
    # Validar y extraer respuestas
    try:
        clarity = int(data['clarity'])
        accessibility = int(data['accessibility'])
        reliability = int(data['reliability'])

        if not (1 <= clarity <= 5 and 1 <= accessibility <= 5 and 1 <= reliability <= 5):
            raise ValueError("Ratings must be between 1 and 5")
    except (KeyError, ValueError, TypeError) as e:
        return jsonify({'error': 'Invalid data'}), 400

    feedback = Feedback(
        user_id=session['user_id'],
        clarity_rating=clarity,
        accessibility_rating=accessibility,
        reliability_rating=reliability
    )
    db.session.add(feedback)
    db.session.commit()

    return jsonify({'success': True})