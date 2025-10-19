from flask import request, jsonify
from model.models import Contact
from model.db import db

def submit_contact():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    subject = data.get('subject')
    message = data.get('message')

    # Validaciones
    if not all([name, email, subject, message]):
        return jsonify({'error': 'Todos los campos son requeridos'}), 400

    if '@' not in email or '.' not in email:
        return jsonify({'error': 'Formato de email inválido'}), 400

    # Crear nuevo contacto
    new_contact = Contact(
        name=name,
        email=email,
        subject=subject,
        message=message
    )

    try:
        db.session.add(new_contact)
        db.session.commit()
        
        return jsonify({
            'message': 'Mensaje enviado exitosamente. Nos pondremos en contacto contigo pronto.',
            'contact_id': new_contact.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error al enviar el mensaje: ' + str(e)}), 500