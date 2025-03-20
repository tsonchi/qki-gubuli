from flask import Flask, render_template, url_for, flash, redirect, request
from __init__ import app, db, bcrypt
from Forms import RegistrationForm, LoginForm
from Models import User, Post
from flask_login import login_user, current_user, logout_user, login_required

@app.route('/')
def method_name():
    pass