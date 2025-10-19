from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from functools import wraps
import json
from controller import moderator_controller

moderator_bp = Blueprint('moderator', __name__)

def moderator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') not in ['moderator', 'administrator']:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@moderator_bp.route('/moderator')
@moderator_required
def moderator_dashboard():
    stats = moderator_controller.get_statistics()
    return render_template(
        'moderator.html',
        **stats,
        avg_ratings_data=json.dumps(stats['avg_ratings_data']),
        distribution_data=json.dumps(stats['distribution_data']),
        university_data=json.dumps(stats['university_data']),
        gender_data=json.dumps(stats['gender_data']),
        academic_data=json.dumps(stats['academic_data']),
        age_data=json.dumps(stats['age_data']),
    )

@moderator_bp.route('/moderator/time_evolution', methods=['GET'])
@moderator_required
def get_time_evolution_data():
    return moderator_controller.get_time_evolution_data()
