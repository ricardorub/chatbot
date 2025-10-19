from .db import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}  # ← Añade esta línea
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    university = db.Column(db.String(100))
    gender = db.Column(db.String(50))
    academic_level = db.Column(db.String(100))
    age = db.Column(db.Integer)
    role = db.Column(db.String(20), nullable=False, default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    chat_sessions = db.relationship('ChatSession', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'


class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'
    __table_args__ = {'extend_existing': True}  # ← Añade esta línea
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), default='Nueva conversación')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    messages = db.relationship('ChatMessage', backref='session', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<ChatSession {self.title}>'


class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    __table_args__ = {'extend_existing': True}  # ← Añade esta línea
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_user = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ChatMessage {self.id}>'


class Contact(db.Model):
    __tablename__ = 'contacts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')

    def __repr__(self):
        return f'<Contact {self.name} - {self.subject}>'


class Feedback(db.Model):
    __tablename__ = 'feedback'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    clarity_rating = db.Column(db.Integer, nullable=False)  # 1 a 5
    accessibility_rating = db.Column(db.Integer, nullable=False)
    reliability_rating = db.Column(db.Integer, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='feedback')

    def __repr__(self):
        return f'<Feedback {self.user.email} - Clarity: {self.clarity_rating}>'