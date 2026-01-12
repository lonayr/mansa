from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class UserCat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    bio = db.Column(db.Text)
    profile_image = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey('user_cat.id'))
    category = db.relationship('UserCat', backref='users')

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    file_url = db.Column(db.String(255))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref='courses')

class CourseVisit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    course = db.relationship('Course', backref='visits')

class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    level = db.Column(db.String(100))
    school = db.Column(db.String(200))
    phone = db.Column(db.String(30))
    birth_date = db.Column(db.Date)
    gender = db.Column(db.String(10))
    city = db.Column(db.String(100))
    user = db.relationship('User', backref='student_profile', uselist=False)

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    platform_name = db.Column(db.String(200), nullable=False)
    platform_description = db.Column(db.Text)
    support_email = db.Column(db.String(200))
    logo_filename = db.Column(db.String(255))
