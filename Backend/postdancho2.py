from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Post

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db.init_app(app)

@app.route('/create_post', methods=['POST'])
@login_required
def create_post():
    content = request.form.get('content')

    if not content:
        flash("Post content cannot be empty!", "danger")
        return redirect(url_for('home'))

    new_post = Post(user_id=current_user.id, username=current_user.username, content=content)
    db.session.add(new_post)
    db.session.commit()

    return redirect(url_for('home'))

@app.route('/home')
def home():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('home.html', posts=posts)
