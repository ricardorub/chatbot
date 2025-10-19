from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from model.models import Feedback, User
from functools import wraps
from model.db import db
from sqlalchemy import func
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
    # Obtener valores para los filtros
    universities = [u[0] for u in db.session.query(User.university).distinct().all() if u[0]]
    genders = [g[0] for g in db.session.query(User.gender).distinct().all() if g[0]]
    academic_levels = [a[0] for a in db.session.query(User.academic_level).distinct().all() if a[0]]

    # Datos para las tarjetas de estadísticas
    total_users = User.query.count()
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
    # 1. Promedio general (ya calculado)
    avg_ratings_data = {
        'labels': ['Claridad', 'Accesibilidad', 'Confianza'],
        'datasets': [{
            'label': 'Puntuación promedio',
            'data': [avg_clarity, avg_accessibility, avg_reliability],
        }]
    }

    # 2. Distribución de ratings
    ratings_distribution = db.session.query(
        func.round((Feedback.clarity_rating + Feedback.accessibility_rating + Feedback.reliability_rating) / 3),
        func.count()
    ).group_by(func.round((Feedback.clarity_rating + Feedback.accessibility_rating + Feedback.reliability_rating) / 3)).all()
    
    distribution_data = {
        'labels': [f'{int(stars)} Estrella(s)' for stars, count in ratings_distribution],
        'datasets': [{
            'data': [count for stars, count in ratings_distribution]
        }]
    }

    # 3. Usuarios por universidad
    users_by_university = db.session.query(User.university, func.count(User.id)).group_by(User.university).order_by(func.count(User.id).desc()).limit(7).all()
    university_data = {
        'labels': [uni[0] for uni in users_by_university],
        'datasets': [{
            'label': 'Usuarios',
            'data': [uni[1] for uni in users_by_university]
        }]
    }

    # 4. Distribución por género
    gender_distribution = db.session.query(User.gender, func.count(User.id)).group_by(User.gender).all()
    gender_data = {
        'labels': [g[0] for g in gender_distribution if g[0]],
        'datasets': [{
            'data': [g[1] for g in gender_distribution if g[0]]
        }]
    }

    # 5. Nivel académico
    academic_level_distribution = db.session.query(User.academic_level, func.count(User.id)).group_by(User.academic_level).all()
    academic_data = {
        'labels': [al[0] for al in academic_level_distribution if al[0]],
        'datasets': [{
            'label': 'Usuarios',
            'data': [al[1] for al in academic_level_distribution if al[0]]
        }]
    }

    # 6. Rango de edad
    age_bins = [
        (18, 24), (25, 34), (35, 44), (45, 54), (55, 100)
    ]
    age_distribution = []
    for min_age, max_age in age_bins:
        count = User.query.filter(User.age.between(min_age, max_age)).count()
        age_distribution.append(count)
    
    age_data = {
        'labels': [f'{min_age}-{max_age}' for min_age, max_age in age_bins],
        'datasets': [{
            'label': 'Usuarios',
            'data': age_distribution
        }]
    }
    
    return render_template(
        'moderator.html', 
        total_users=total_users,
        general_avg=f'{general_avg:.2f}',
        universities_count=universities_count,
        satisfaction=f'{(general_avg / 5 * 100):.0f}%' if general_avg > 0 else '0%',
        
        # Datos para los filtros
        universities=universities,
        genders=genders,
        academic_levels=academic_levels,

        # Datos para gráficos en formato JSON
        avg_ratings_data=json.dumps(avg_ratings_data),
        distribution_data=json.dumps(distribution_data),
        university_data=json.dumps(university_data),
        gender_data=json.dumps(gender_data),
        academic_data=json.dumps(academic_data),
        age_data=json.dumps(age_data),
    )

@moderator_bp.route('/moderator/time_evolution', methods=['GET'])
@moderator_required
def get_time_evolution_data():
    return moderator_controller.get_time_evolution_data()
