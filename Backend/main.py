from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask import render_template, url_for, flash, redirect, request
from flask_bcrypt import Bcrypt
from flask_login import login_user, current_user, logout_user

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
DB = SQLAlchemy(app)
login_manager = LoginManager(app)
bcrypt=Bcrypt(app)


@app.route('/')
@app.route('/home')
def homepage():
    return render_template('index.html')

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

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
    submit = SubmitField('Login')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('homepage'))
    form = RegistrationForm()
    print(form.password.data)
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        DB.session.add(user)
        DB.session.commit()
        flash('Your account has been created', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html',form=form)



@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('homepage'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user,remember=form.remember.data)
            return redirect(url_for('homepage'))
        else:
            flash('Login Unsuccessful. Please check email and password.')
    return render_template('login.html',form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('homepage'))

@app.route("/search")
def search():
    return render_template('input.html')


from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin,DB.Model):
    id = DB.Column(DB.Integer,primary_key=True)
    username = DB.Column(DB.String(20),unique=True,nullable=False)
    email = DB.Column(DB.String(100),unique=True,nullable=False)
    password = DB.Column(DB.String(50),nullable=False)
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

if __name__ == '__main__':
    with app.app_context():
        DB.create_all()
    app.run(debug=True)
