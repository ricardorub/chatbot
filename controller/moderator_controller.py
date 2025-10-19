from flask import jsonify, session
from model.models import User, Feedback, ChatSession
from model.db import db
from sqlalchemy import func
from datetime import datetime, timedelta

def get_statistics():
    # Datos para las tarjetas de estadísticas
    total_users = User.query.count()
    universities = [u[0] for u in db.session.query(User.university).distinct().all() if u[0]]
    universities_count = len(universities)
    
    feedback_list = Feedback.query.all()
    total_feedback = len(feedback_list)
    
    if total_feedback > 0:
        avg_clarity = sum(f.clarity_rating for f in feedback_list) / total_feedback
        avg_accessibility = sum(f.accessibility_rating for f in feedback_list) / total_feedback
        avg_reliability = sum(f.reliability_rating for f in feedback_list) / total_feedback
        general_avg = (avg_clarity + avg_accessibility + avg_reliability) / 3
    else:
        avg_clarity = avg_accessibility = avg_reliability = general_avg = 0

    # Datos para los gráficos
    avg_ratings_data = {
        'labels': ['Claridad', 'Accesibilidad', 'Confianza'],
        'datasets': [{'label': 'Puntuación promedio', 'data': [avg_clarity, avg_accessibility, avg_reliability]}]
    }

    ratings_distribution = db.session.query(
        func.round((Feedback.clarity_rating + Feedback.accessibility_rating + Feedback.reliability_rating) / 3),
        func.count()
    ).group_by(func.round((Feedback.clarity_rating + Feedback.accessibility_rating + Feedback.reliability_rating) / 3)).all()
    
    distribution_data = {
        'labels': [f'{int(stars)} Estrella(s)' for stars, count in ratings_distribution],
        'datasets': [{'data': [count for stars, count in ratings_distribution]}]
    }

    users_by_university = db.session.query(User.university, func.count(User.id)).group_by(User.university).order_by(func.count(User.id).desc()).limit(7).all()
    university_data = {
        'labels': [uni[0] for uni in users_by_university],
        'datasets': [{'label': 'Usuarios', 'data': [uni[1] for uni in users_by_university]}]
    }

    gender_distribution = db.session.query(User.gender, func.count(User.id)).group_by(User.gender).all()
    gender_data = {
        'labels': [g[0] for g in gender_distribution if g[0]],
        'datasets': [{'data': [g[1] for g in gender_distribution if g[0]]}]
    }

    academic_level_distribution = db.session.query(User.academic_level, func.count(User.id)).group_by(User.academic_level).all()
    academic_data = {
        'labels': [al[0] for al in academic_level_distribution if al[0]],
        'datasets': [{'label': 'Usuarios', 'data': [al[1] for al in academic_level_distribution if al[0]]}]
    }

    age_bins = [(18, 24), (25, 34), (35, 44), (45, 54), (55, 100)]
    age_distribution = [User.query.filter(User.age.between(min_age, max_age)).count() for min_age, max_age in age_bins]
    
    age_data = {
        'labels': [f'{min_age}-{max_age}' for min_age, max_age in age_bins],
        'datasets': [{'label': 'Usuarios', 'data': age_distribution}]
    }
    
    return {
        'feedback_list': feedback_list,
        'total_users': total_users,
        'general_avg': f'{general_avg:.2f}',
        'universities_count': universities_count,
        'satisfaction': f'{(general_avg / 5 * 100):.0f}%' if general_avg > 0 else '0%',
        'universities': universities,
        'genders': [g[0] for g in db.session.query(User.gender).distinct().all() if g[0]],
        'academic_levels': [a[0] for a in db.session.query(User.academic_level).distinct().all() if a[0]],
        'avg_ratings_data': avg_ratings_data,
        'distribution_data': distribution_data,
        'university_data': university_data,
        'gender_data': gender_data,
        'academic_data': academic_data,
        'age_data': age_data,
    }

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
