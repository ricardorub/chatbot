from flask import Blueprint
from controller import auth_controller

auth_bp = Blueprint('auth', __name__)

auth_bp.route('/login', methods=['POST'])(auth_controller.login)
auth_bp.route('/logout', methods=['GET', 'POST'])(auth_controller.logout)
auth_bp.route('/register', methods=['POST'])(auth_controller.register)