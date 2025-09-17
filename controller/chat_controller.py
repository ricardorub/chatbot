from flask import request, jsonify, render_template, session, redirect, url_for
from model.models import ChatSession, ChatMessage
from model.db import db
from datetime import datetime

def get_bot_response(user_message):
    # Simple echo response for now
    return f"This is a response to: {user_message}"

def chat():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        data = request.get_json()
        message_text = data.get('message')
        session_id = data.get('session_id')

        if not message_text or not session_id:
            return jsonify({'error': 'Missing message or session_id'}), 400

        # Save user message
        user_message = ChatMessage(session_id=session_id, sender='user', message=message_text)
        db.session.add(user_message)

        # Get bot response
        bot_response_text = get_bot_response(message_text)
        bot_message = ChatMessage(session_id=session_id, sender='bot', message=bot_response_text)
        db.session.add(bot_message)
        
        db.session.commit()

        return jsonify({'reply': bot_response_text})

    # For GET request, render the chat page
    return index()


def index():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    sessions = ChatSession.query.filter_by(user_id=user_id).order_by(ChatSession.created_at.desc()).all()

    if not sessions:
        new_session = ChatSession(user_id=user_id, title="Nueva conversación")
        db.session.add(new_session)
        db.session.commit()
        sessions = [new_session]

    return render_template('chat2.html', sessions=sessions, current_session=sessions[0], messages=sessions[0].messages)


def new_chat():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    new_session = ChatSession(user_id=user_id, title="Nueva conversación")
    db.session.add(new_session)
    db.session.commit()

    return jsonify({
        'id': new_session.id,
        'title': new_session.title,
        'created_at': new_session.created_at.strftime('%Y-%m-%d %H:%M')
    })


def load_chat(session_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
        
    session_obj = ChatSession.query.get_or_404(session_id)

    if session_obj.user_id != user_id:
        return redirect(url_for('chat.index'))

    messages = session_obj.messages
    sessions = ChatSession.query.filter_by(user_id=user_id).order_by(ChatSession.created_at.desc()).all()

    return render_template('chat2.html',
                           sessions=sessions,
                           current_session=session_obj,
                           messages=messages)


def update_title(session_id):
    data = request.get_json()
    new_title = data.get('title', '').strip()
    user_id = session.get('user_id')

    session_obj = ChatSession.query.get_or_404(session_id)
    if session_obj.user_id != user_id:
        return jsonify({'error': 'Access denied'}), 403

    session_obj.title = new_title or "Nueva conversación"
    db.session.commit()

    return jsonify({'success': True, 'title': session_obj.title})


def delete_chat(session_id):
    user_id = session.get('user_id')
    session_obj = ChatSession.query.get_or_404(session_id)
    if session_obj.user_id != user_id:
        return jsonify({'error': 'Access denied'}), 403

    db.session.delete(session_obj)
    db.session.commit()

    return jsonify({'success': True})
