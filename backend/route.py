from flask import Flask, render_template, url_for, flash, redirect, request
from __init__ import app, DB, bcrypt
from Forms import RegistrationForm, LoginForm
from Models import User
from flask_login import login_user, current_user, logout_user, login_required

@app.route('/')
@app.route('/home')
def homepage():
    return app.send_static_file('index.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('homepage'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        DB.session.add(user)
        DB.session.commit()
        flash('Your account has been created', 'success')
        return redirect(url_for('login'))
    return app.send_static_file('signup.html')



@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('homepage'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return app.send_static_file('login.html')


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('homepage'))

@app.route("/search")
def search():
    return app.send_static_file('input.html')
