from flask import render_template, session, request, jsonify
from model.models import User, ChatSession, ChatMessage
from model.db import db
from datetime import datetime

def index():
    # Verificar si el usuario está logueado
    user = None
    if 'user_id' in session:
        user = {'email': session.get('user_email')}
        
        # Obtener las sesiones de chat del usuario actual
        chat_sessions = ChatSession.query.filter_by(user_id=session['user_id']).order_by(ChatSession.created_at.desc()).all()
        
        # Obtener la sesión actual si existe
        current_session = None
        if chat_sessions:
            current_session = chat_sessions[0]  # La más reciente por defecto
            
        return render_template('chat2.html', 
                             user=user, 
                             chat_sessions=chat_sessions,
                             current_session=current_session)
    else:
        # Si no está logueado, redirigir al inicio
        return render_template('index.html', user=user)