from flask import Blueprint
from controller import contact_controller

contact_bp = Blueprint('contact', __name__)

contact_bp.route('/api/contact', methods=['POST'])(contact_controller.submit_contact)