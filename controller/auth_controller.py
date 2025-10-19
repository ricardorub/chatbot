from flask import request, jsonify, session, redirect, url_for
from model.models import User
from model.db import db

def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email y contraseña son requeridos'}), 400

    user = User.query.filter_by(email=email).first()

    if user and user.password == password:
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['user_first_name'] = user.first_name or ''
        session['user_last_name'] = user.last_name or ''
        session['user_role'] = user.role
        
        return jsonify({
            'message': 'Login exitoso', 
            'user': {
                'id': user.id, 
                'email': user.email,
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'role': user.role
            },
            'redirect': '/chat'
        }), 200
    else:
        return jsonify({'error': 'Credenciales inválidas'}), 401

def logout():
    session.clear()
    return redirect(url_for('index'))

def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()

    if not email or not password:
        return jsonify({'error': 'Email y contraseña son requeridos'}), 400

    # Validar formato de email
    if '@' not in email or '.' not in email:
        return jsonify({'error': 'Formato de email inválido'}), 400

    # Verificar si el usuario ya existe
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'El usuario ya existe'}), 400

    # Crear nuevo usuario
    new_user = User(
        email=email,
        password=password,
        first_name=first_name if first_name else None,
        last_name=last_name if last_name else None
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        
        # Iniciar sesión automáticamente después del registro
        session['user_id'] = new_user.id
        session['user_email'] = new_user.email
        session['user_first_name'] = new_user.first_name or ''
        session['user_last_name'] = new_user.last_name or ''
        session['user_role'] = new_user.role
        
        return jsonify({
            'message': 'Usuario registrado exitosamente',
            'user': {
                'id': new_user.id,
                'email': new_user.email,
                'first_name': new_user.first_name,
                'last_name': new_user.last_name,
                'role': new_user.role
            },
            'redirect': '/chat'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error al crear el usuario: ' + str(e)}), 500