from flask import request, redirect, url_for, render_template, session, flash, jsonify
from model.models import User
from model.db import db

def login():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            username = data['username']
            password = data['password']
        else:
            username = request.form['username']
            password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            session['user_id'] = user.id
            session['username'] = user.username
            if request.is_json:
                return jsonify({'success': True, 'redirect': url_for('chat.index')})
            return redirect(url_for('chat.index'))
        else:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Invalid username or password'})
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))

    return render_template('login.html')

def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        first_name = request.form['firstName']
        last_name = request.form['lastName']
        
        new_user = User(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('You have successfully registered!')
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')

def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('auth.login'))