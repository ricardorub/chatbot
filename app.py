from flask import Flask, redirect, url_for, session, render_template, request
from model.db import db
from routes.auth import auth_bp
from routes.chat import chat_bp

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost/chatbot_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Initialize DB
db.init_app(app)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)

@app.route('/')
def index():
    # MOSTRAR SIEMPRE INDEX.HTML, NO REDIRIGIR AUTOMÁTICAMENTE
    user = None
    if 'user_id' in session:
        user = {
            'email': session.get('user_email'),
            'first_name': session.get('user_first_name', ''),
            'last_name': session.get('user_last_name', '')
        }
    return render_template('index.html', user=user)

@app.route('/home')
def home():
    """Redirigir a chat solo si se accede explícitamente a /home"""
    if 'user_id' in session:
        return redirect('/chat')
    else:
        return redirect('/')

@app.route('/reset-db')
def reset_db():
    try:
        from model.models import User, ChatSession, ChatMessage
        with app.app_context():
            db.drop_all()
            db.create_all()
            
            # Crear usuario de prueba
            test_user = User(
                email='test@example.com',
                password='password123',
                first_name='Test',
                last_name='User'
            )
            db.session.add(test_user)
            db.session.commit()
            
        return "Database has been reset and test user created."
    except Exception as e:
        return f"An error occurred while resetting the database: {e}"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')