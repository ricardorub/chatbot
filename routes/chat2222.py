from flask import Blueprint, render_template, session, redirect, request, jsonify
from model.models import ChatSession, ChatMessage, User
from model.db import db
from datetime import datetime

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat')
def chat():
    # Verificar si el usuario está logueado
    if 'user_id' not in session:
        return redirect('/')
    
    user = {'email': session.get('user_email')}
    chat_sessions = ChatSession.query.filter_by(user_id=session['user_id']).order_by(ChatSession.created_at.desc()).all()
    
    # Crear una sesión por defecto si no existe
    if not chat_sessions:
        new_session = ChatSession(
            user_id=session['user_id'],
            title='Nueva conversación'
        )
        db.session.add(new_session)
        db.session.commit()
        chat_sessions = [new_session]
    
    current_session = chat_sessions[0]
    
    return render_template('chat2.html', 
                         user=user, 
                         chat_sessions=chat_sessions,
                         current_session=current_session)

@chat_bp.route('/api/chat/load/<int:session_id>', methods=['GET'])
def load_chat(session_id):
    """Cargar mensajes de una sesión específica"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    # Verificar que la sesión pertenezca al usuario
    chat_session = ChatSession.query.filter_by(id=session_id, user_id=session['user_id']).first()
    if not chat_session:
        return jsonify({'error': 'Sesión no encontrada'}), 404
    
    # Obtener los mensajes de la sesión
    messages = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.created_at.asc()).all()
    
    return jsonify({
        'messages': [{
            'id': msg.id,
            'message': msg.message,
            'is_user': msg.is_user,
            'created_at': msg.created_at.isoformat()
        } for msg in messages]
    }), 200

@chat_bp.route('/api/chat/send', methods=['POST'])
def send_message():
    """Enviar un nuevo mensaje"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    data = request.get_json()
    message = data.get('message')
    session_id = data.get('session_id')
    
    if not message:
        return jsonify({'error': 'El mensaje no puede estar vacío'}), 400
    
    # Crear o obtener la sesión
    if not session_id:
        # Crear nueva sesión
        new_session = ChatSession(
            user_id=session['user_id'],
            title=message[:50] + '...' if len(message) > 50 else message
        )
        db.session.add(new_session)
        db.session.flush()  # Para obtener el ID sin hacer commit
        session_id = new_session.id
    
    # Crear el mensaje
    new_message = ChatMessage(
        session_id=session_id,
        message=message,
        is_user=True
    )
    db.session.add(new_message)
    db.session.commit()
    
    # Obtener la sesión actualizada
    chat_session = ChatSession.query.get(session_id)
    
    return jsonify({
        'message': 'Mensaje enviado',
        'session_id': session_id,
        'session_title': chat_session.title
    }), 200

@chat_bp.route('/api/chat/delete/<int:session_id>', methods=['DELETE'])
def delete_chat(session_id):
    """Eliminar una sesión de chat"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    # Verificar que la sesión pertenezca al usuario
    chat_session = ChatSession.query.filter_by(id=session_id, user_id=session['user_id']).first()
    if not chat_session:
        return jsonify({'error': 'Sesión no encontrada'}), 404
    
    # Eliminar la sesión (y los mensajes por cascade)
    db.session.delete(chat_session)
    db.session.commit()
    
    return jsonify({'message': 'Sesión eliminada'}), 200

@chat_bp.route('/api/chat/sessions', methods=['GET'])
def get_sessions():
    """Obtener todas las sesiones del usuario"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    chat_sessions = ChatSession.query.filter_by(user_id=session['user_id']).order_by(ChatSession.created_at.desc()).all()
    
    return jsonify({
        'sessions': [{
            'id': session.id,
            'title': session.title,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat()
        } for session in chat_sessions]
    }), 200

@chat_bp.route('/api/chat/switch/<int:session_id>', methods=['POST'])
def switch_chat(session_id):
    """Cambiar a una sesión específica"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    # Verificar que la sesión pertenezca al usuario
    chat_session = ChatSession.query.filter_by(id=session_id, user_id=session['user_id']).first()
    if not chat_session:
        return jsonify({'error': 'Sesión no encontrada'}), 404
    
    return jsonify({
        'message': 'Sesión cambiada',
        'session': {
            'id': chat_session.id,
            'title': chat_session.title
        }
    }), 200