from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask import render_template, url_for, flash, redirect, request, abort
from flask_bcrypt import Bcrypt
from flask_login import login_user, current_user, logout_user,login_required

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
FASTAPI_URL = "http://127.0.0.1:8000/plan_route/"
DB = SQLAlchemy(app)
login_manager = LoginManager(app)
bcrypt=Bcrypt(app)


@app.route('/')
@app.route('/home')
def home():
    post=Posts.query.all()
    return render_template('index.html',post=posts)

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, BooleanField,TextAreaField
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
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')
    
class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    image = FileField('Upload Image', validators=[FileRequired(),FileAllowed(['jpg','png','jpeg'])])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Post')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    print(form.password.data)
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        DB.session.add(user)
        DB.session.commit()
        flash('Your account has been created!')
        return redirect(url_for('login'))
    return render_template('signup.html',form=form)



@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user,remember=form.remember.data)
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password.')
    return render_template('login.html',form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/about')
def about_page():
    return render_template('about.html')

@app.route('/contact')
def contact_page():
    return render_template('contact.html')

@app.route("/search")
def search():
    return render_template('input.html')

import requests

@app.route("/plan_route", methods=["GET", "POST"])
def plan_route():
    if request.method == "POST":
        city = request.form.get("city")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")

        print(f"📌 Sending request to FastAPI with: city={city}, start_date={start_date}, end_date={end_date}")

        try:
            response = requests.get(FASTAPI_URL, params={
                "city": city,
                "start_date": start_date,
                "end_date": end_date
            })
            response.raise_for_status()  

            data = response.json()  
            print(f"Received response from FastAPI: {data}")

            if "error" in data:
                flash(data["error"], "danger")
                return redirect(url_for('plan_route'))
            
            print(f"🚀 Rendering data: {data['data']}")

            return render_template("plan_route.html", data=data["data"]) 

        except requests.exceptions.RequestException as e:
            flash(f"An error occurred: {e}", "danger")
            return redirect(url_for("plan_route"))

    return render_template("plan_route.html")



from flask import request, flash, redirect, url_for

@app.route('/create_post', methods=['POST', 'GET'])
@login_required
def create_post():
    content = request.form.get('content')

    if not content:
        flash("Post content cannot be empty", "danger")
        return render_template('create_post.html',post=posts, title='Create Post', legend='Create Post')  

    new_post = Posts(content=content, user_id=current_user.id)
    
    try:
        DB.session.add(new_post)
        DB.session.commit()
        flash("Post created successfully!", "success")
        print("Post created successfully!")
        return redirect('/home')
        
    except Exception as e:
        DB.session.rollback()
        flash("Error creating post: " + str(e), "danger")
        print("Error creating post: " + str(e))
        return redirect(url_for('home'))

    return redirect(url_for("home"))

@app.route("/post/<int:post_id>")
def posts(post_id):
    post = Posts.query.get_or_404(post_id)
    return render_template('posts.html', title=post.title, post=post)

from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin,DB.Model):
    id = DB.Column(DB.Integer,primary_key=True)
    username = DB.Column(DB.String(20),unique=True,nullable=False)
    email = DB.Column(DB.String(100),unique=True,nullable=False)
    password = DB.Column(DB.String(50),nullable=False)
    posts = DB.relationship('Posts',backref='author',lazy=True)
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"
    
class Posts(DB.Model):
    id = DB.Column(DB.Integer,primary_key=True)
    content = DB.Column(DB.Text,nullable=False)
    image_file = DB.Column(DB.String(20),nullable=True)
    date_posted = DB.Column(DB.DateTime,nullable=False,default=datetime.utcnow)
    user_id = DB.Column(DB.Integer, DB.ForeignKey('user.id'),nullable=False)
    
    def __repr__(self):
        return f"Posts('{self.title}', '{self.date_posted}')"

if __name__ == '__main__':
    with app.app_context():
        DB.create_all()
    app.run(debug=True)
