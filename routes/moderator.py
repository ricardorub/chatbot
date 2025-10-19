from flask import Blueprint, render_template, session, redirect, url_for
from model.models import Feedback, User
from functools import wraps

moderator_bp = Blueprint('moderator', __name__)

def moderator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') != 'moderator':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@moderator_bp.route('/moderator')
@moderator_required
def moderator_dashboard():
    feedback_list = Feedback.query.join(User).all()
    return render_template('moderator.html', feedback_list=feedback_list)