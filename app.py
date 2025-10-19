from flask import Flask, redirect, url_for, session, render_template, request
from model.db import db
from routes.auth import auth_bp
from routes.chat import chat_bp
from routes.contact import contact_bp
from routes.moderator import moderator_bp
from routes.feedback import feedback_bp

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost/chatbot_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Initialize DB
db.init_app(app)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(contact_bp)
app.register_blueprint(moderator_bp)
app.register_blueprint(feedback_bp)

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
        from model.models import User, ChatSession, ChatMessage, Contact
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

            # Crear usuario moderador
            moderator_user = User(
                email='moderator@example.com',
                password='password123',
                first_name='Moderator',
                last_name='User',
                role='moderator'
            )
            db.session.add(moderator_user)
            
            db.session.commit()
            
        return "Database has been reset and test users created."
    except Exception as e:
        return f"An error occurred while resetting the database: {e}"

@app.route('/test-contact')
def test_contact():
    """Página de prueba para el formulario de contacto"""
    return """
    <h1>Prueba del Formulario de Contacto</h1>
    <form id="testForm">
        <input type="text" name="name" placeholder="Nombre" required><br>
        <input type="email" name="email" placeholder="Email" required><br>
        <input type="text" name="subject" placeholder="Asunto" required><br>
        <textarea name="message" placeholder="Mensaje" required></textarea><br>
        <button type="submit">Enviar</button>
    </form>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script>
        $('#testForm').submit(function(e) {
            e.preventDefault();
            const formData = $(this).serializeArray();
            const data = {};
            formData.forEach(item => { data[item.name] = item.value; });
            
            $.ajax({
                url: '/api/contact',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(data),
                success: function(response) {
                    alert('Éxito: ' + response.message);
                },
                error: function(xhr) {
                    alert('Error: ' + (xhr.responseJSON?.error || 'Error desconocido'));
                }
            });
        });
    </script>
    """

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')