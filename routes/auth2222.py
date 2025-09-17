from flask import request, jsonify, session
from model.models import User
from model.db import db

def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email y contraseña son requeridos'}), 400

    user = User.query.filter_by(email=email).first()

    if user and user.password == password:  # Comparación directa en texto plano
        session['user_id'] = user.id
        session['user_email'] = user.email
        return jsonify({
            'message': 'Login exitoso', 
            'user': {
                'id': user.id, 
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        }), 200
    else:
        return jsonify({'error': 'Credenciales inválidas'}), 401

def logout():
    session.clear()
    return jsonify({'message': 'Logout exitoso'}), 200

def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')

    if not email or not password:
        return jsonify({'error': 'Email y contraseña son requeridos'}), 400

    # Verificar si el usuario ya existe
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'El usuario ya existe'}), 400

    # Crear nuevo usuario
    new_user = User(
        email=email,
        password=password,  # Almacenar en texto plano
        first_name=first_name,
        last_name=last_name
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        'message': 'Usuario registrado exitosamente',
        'user': {
            'id': new_user.id,
            'email': new_user.email,
            'first_name': new_user.first_name,
            'last_name': new_user.last_name
        }
    }), 201