from flask import Blueprint, request
from controller import admin_controller
from controller.auth_controller import admin_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/users', methods=['GET'])
@admin_required
def get_admins_and_mods():
    return admin_controller.get_admins_and_mods()

@admin_bp.route('/admin/users/<int:user_id>/role', methods=['PUT'])
@admin_required
def change_user_role(user_id):
    new_role = request.json.get('role')
    return admin_controller.change_user_role(user_id, new_role)

@admin_bp.route('/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    return admin_controller.delete_user(user_id)