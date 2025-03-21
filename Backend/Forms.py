from datetime import datetime
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, BooleanField,TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from Models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username',validators=[DataRequired(),Length(min=2,max=20)])
    email = StringField('Email',validators=[DataRequired(),Email()])
    password = PasswordField('Password',validators=[DataRequired()])
    confirm_password = PasswordField('Confirm password',validators=[DataRequired(),EqualTo('password')])
    submit = SubmitField('Sign up')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please enter a new one.')
        
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')
        
        
class LoginForm(FlaskForm):
    email = StringField('Email',validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')
    
class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    image = FileField('Upload Image', validators=[FileRequired(),FileAllowed(['jpg','png','jpeg'])])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Post')