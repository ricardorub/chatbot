from flask import Flask, redirect, url_for, session
from model.db import db
from routes.auth import auth_bp
from routes.chat import chat_bp

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/chatbot_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Initialize DB
db.init_app(app)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)

@app.route('/reset-db')
def reset_db():
    try:
        # The models need to be imported for create_all to see them.
        from model.models import User, ChatSession, ChatMessage
        with app.app_context():
            db.drop_all()
            db.create_all()
        return "Database has been reset."
    except Exception as e:
        return f"An error occurred while resetting the database: {e}"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
