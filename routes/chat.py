from flask import Blueprint
from controller import chat_controller

chat_bp = Blueprint('chat', __name__)

chat_bp.route('/')(chat_controller.index)
chat_bp.route('/new_chat', methods=['POST'])(chat_controller.new_chat)
chat_bp.route('/load_chat/<int:session_id>')(chat_controller.load_chat)
chat_bp.route('/update_title/<int:session_id>', methods=['POST'])(chat_controller.update_title)
chat_bp.route('/delete_chat/<int:session_id>', methods=['POST'])(chat_controller.delete_chat)
chat_bp.route('/chat', methods=['POST'])(chat_controller.chat)

