from flask import jsonify, session
from model.models import User
from model.db import db

def get_admins_and_mods():
    if session.get('user_role') != 'administrator':
        return jsonify({'error': 'Unauthorized'}), 403

    admins = User.query.filter_by(role='administrator').all()
    moderators = User.query.filter_by(role='moderator').all()

    admin_list = [{'id': user.id, 'email': user.email, 'first_name': user.first_name, 'last_name': user.last_name} for user in admins]
    moderator_list = [{'id': user.id, 'email': user.email, 'first_name': user.first_name, 'last_name': user.last_name} for user in moderators]

    return jsonify({'administrators': admin_list, 'moderators': moderator_list}), 200

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