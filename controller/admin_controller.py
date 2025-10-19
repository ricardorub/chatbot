from flask import jsonify, session
from model.models import User
from model.db import db

def get_all_users():
    if session.get('user_role') != 'administrator':
        return jsonify({'error': 'Unauthorized'}), 403

    users = User.query.all()
    users_list = [{'id': u.id, 'email': u.email, 'first_name': u.first_name, 'last_name': u.last_name, 'role': u.role} for u in users]
    
    return jsonify(users=users_list)

def change_user_role(user_id, new_role):
    if session.get('user_role') != 'administrator':
        return jsonify({'error': 'Unauthorized'}), 403

    if new_role not in ['administrator', 'moderator', 'user']:
        return jsonify({'error': 'Invalid role'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user.role = new_role
    db.session.commit()
    return jsonify({'message': f'User role updated to {new_role}'}), 200

def delete_user(user_id):
    if session.get('user_role') != 'administrator':
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    if user.email == 'superuser@gmail.com':
        return jsonify({'error': 'Cannot delete superuser'}), 403

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'}), 200
