from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/chatbot_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'



@app.route('/')
def index():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')  # Asegúrate de tener login

    # Obtener todas las sesiones del usuario
    sessions = ChatSession.query.filter_by(user_id=user_id).order_by(ChatSession.created_at.desc()).all()

    # Si no hay sesiones, crear una nueva por defecto
    if not sessions:
        new_session = ChatSession(user_id=user_id, title="Nueva conversación")
        db.session.add(new_session)
        db.session.commit()
        sessions = [new_session]

    return render_template('chat.html', sessions=sessions, current_session=None)



@app.route('/new_chat', methods=['POST'])
def new_chat():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'No autenticado'}), 401

    new_session = ChatSession(user_id=user_id, title="Nueva conversación")
    db.session.add(new_session)
    db.session.commit()

    return jsonify({
        'id': new_session.id,
        'title': new_session.title,
        'created_at': new_session.created_at.strftime('%Y-%m-%d %H:%M')
    })




@app.route('/load_chat/<int:session_id>')
def load_chat(session_id):
    user_id = session.get('user_id')
    session_obj = ChatSession.query.get_or_404(session_id)

    if session_obj.user_id != user_id:
        return redirect(url_for('index'))

    messages = session_obj.messages.order_by(ChatMessage.timestamp).all()

    return render_template('chat.html', 
                           sessions=ChatSession.query.filter_by(user_id=user_id).all(),
                           current_session=session_obj,
                           messages=messages)



@app.route('/update_title/<int:session_id>', methods=['POST'])
def update_title(session_id):
    data = request.get_json()
    new_title = data.get('title', '').strip()

    session_obj = ChatSession.query.get_or_404(session_id)
    if session_obj.user_id != session.get('user_id'):
        return jsonify({'error': 'Acceso denegado'}), 403

    session_obj.title = new_title or "Nueva conversación"
    db.session.commit()

    return jsonify({'success': True, 'title': session_obj.title})


@app.route('/delete_chat/<int:session_id>', methods=['POST'])
def delete_chat(session_id):
    session_obj = ChatSession.query.get_or_404(session_id)
    if session_obj.user_id != session.get('user_id'):
        return jsonify({'error': 'Acceso denegado'}), 403

    db.session.delete(session_obj)
    db.session.commit()

    return jsonify({'success': True})