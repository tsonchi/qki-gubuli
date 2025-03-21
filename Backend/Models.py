from flask_login import UserMixin
from datetime import datetime
from main import DB,login_manager

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
    
class Posts(DB.Model):
    id = DB.Column(DB.Integer,primary_key=True)
    title = DB.Column(DB.String(100),nullable=False)
    content = DB.Column(DB.Text,nullable=False)
    image_file = DB.Column(DB.String(20),nullable=False)
    date_posted = DB.Column(DB.DateTime,nullable=False,default=datetime.utcnow)
    user_id = DB.Column(DB.Integer, DB.ForeignKey('user.id'),nullable=False)
    
    def __repr__(self):
        return f"Posts('{self.title}', '{self.date_posted}')"