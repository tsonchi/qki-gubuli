from datetime import datetime
from flask_login import UserMixin
from __init__ import DB,login_manager

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
    