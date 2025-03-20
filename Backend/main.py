from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask import render_template, url_for, flash, redirect, request,abort
from flask_bcrypt import Bcrypt
from flask_login import login_user, current_user, logout_user,login_required

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
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Post')


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
        flash('Your account has been created!')
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

@app.route('/about')
def about_page():
    return render_template('about.html')

@app.route("/search")
def search():
    return render_template('input.html')

@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Posts(title=form.title.data, content=form.content.data, author=current_user)
        DB.session.add(post)
        DB.session.commit()
        flash('Your post has been created!')
        return redirect(url_for('homepage'))
    return render_template('create_post.html', title='New Post',form=form, legend='New Post')

@app.route("/post/<int:post_id>")
def posts(post_id):
    post = Posts.query.get_or_404(post_id)
    return render_template('posts.html', title=post.title, post=post)

def update_post(post_id):
    post = Posts.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        DB.session.commit()
        flash('Your post has been updated!')
        return redirect(url_for('posts', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Posts.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    DB.session.delete(post)
    DB.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('homepage'))

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
    title = DB.Column(DB.String(100),nullable=False)
    content = DB.Column(DB.Text,nullable=False)
    date_posted = DB.Column(DB.DateTime,nullable=False,default=datetime.utcnow)
    user_id = DB.Column(DB.Integer, DB.ForeignKey('user.id'),nullable=False)
    
    def __repr__(self):
        return f"Posts('{self.title}', '{self.date_posted}')"

if __name__ == '__main__':
    with app.app_context():
        DB.create_all()
    app.run(debug=True)
