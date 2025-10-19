from flask import jsonify, session
from model.models import User, Feedback, ChatSession
from model.db import db
from sqlalchemy import func
from datetime import datetime, timedelta

def get_time_evolution_data():
    if session.get('user_role') not in ['administrator', 'moderator']:
        return jsonify({'error': 'Unauthorized'}), 403

    # Define the time range (e.g., last 30 days)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)

    # Query for user creation data
    user_data = db.session.query(func.date(User.created_at), func.count(User.id)) \
        .filter(User.created_at >= start_date) \
        .group_by(func.date(User.created_at)) \
        .order_by(func.date(User.created_at)) \
        .all()

    # Query for feedback submission data
    feedback_data = db.session.query(func.date(Feedback.submitted_at), func.count(Feedback.id)) \
        .filter(Feedback.submitted_at >= start_date) \
        .group_by(func.date(Feedback.submitted_at)) \
        .order_by(func.date(Feedback.submitted_at)) \
        .all()

    # Query for chat session creation data
    chatsession_data = db.session.query(func.date(ChatSession.created_at), func.count(ChatSession.id)) \
        .filter(ChatSession.created_at >= start_date) \
        .group_by(func.date(ChatSession.created_at)) \
        .order_by(func.date(ChatSession.created_at)) \
        .all()

    # Process data for Chart.js
    labels = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(31)]
    users = [0] * 31
    feedbacks = [0] * 31
    chatsessions = [0] * 31

    for date, count in user_data:
        if date:
            day_index = (date - start_date.date()).days
            if 0 <= day_index < 31:
                users[day_index] = count
    
    for date, count in feedback_data:
        if date:
            day_index = (date - start_date.date()).days
            if 0 <= day_index < 31:
                feedbacks[day_index] = count

    for date, count in chatsession_data:
        if date:
            day_index = (date - start_date.date()).days
            if 0 <= day_index < 31:
                chatsessions[day_index] = count

    return jsonify({
        'labels': labels,
        'users': users,
        'feedbacks': feedbacks,
        'chatsessions': chatsessions
    })
