from . import db  # This will work after the import order is fixed in __init__.py
from flask_login import UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DateTimeField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Ensure autoincrement is enabled
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email_address = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(10), default='Student')  # Role is now a string





class Response(db.Model):
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), primary_key=True)
    response = db.Column(db.Integer, nullable=False)

class UserCourse(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), primary_key=True)

class Evaluation(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    answered_count = db.Column(db.Integer, nullable=False)
    corrected_count = db.Column(db.Integer, nullable=False)
    grade = db.Column(db.Integer, nullable=False)
    pass_or_fail = db.Column(db.Boolean, nullable=False)


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Teacher who created the course
    questions = db.relationship('Question', backref='course', lazy=True)  # Link questions to courses

# Question model
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(500), nullable=False)
    difficulty = db.Column(db.String(10), nullable=False)  # 'easy', 'medium', 'hard'
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))  # Associate with course
    added_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # Teacher who added the question
    answers = db.relationship('Answer', backref='question', lazy=True, cascade='all, delete-orphan')  # Cascade delete

# Answer model
class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    answer_text = db.Column(db.String(200), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))  # Link to question
    is_correct = db.Column(db.Boolean, default=False)  # Indicates if this is the correct answer


class Exam(db.Model):
    # __tablename__ = 'exam'  # Optional but a good practice
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    number_of_questions = db.Column(db.Integer, nullable=False)
    passing_grade = db.Column(db.Integer, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_scheduled = db.Column(db.DateTime)
    duration = db.Column(db.Integer)  # Duration in minutes

    # Define relationship without conflicting backref
    exam_questions = db.relationship('ExamQuestion', backref='exam_instance', lazy=True)  # Changed to avoid name conflict


class ExamQuestion(db.Model):
    # __tablename__ = 'exam_question'  # Optional but a good practice
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)  # Add course_id as a foreign key
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)

    # Define relationships
    exam = db.relationship('Exam', backref='exam_questions_rel', lazy=True)  # Keep this to access the exam from the question
    question = db.relationship('Question', backref=db.backref('exam_questions', lazy=True))
    course = db.relationship('Course', backref=db.backref('exam_questions', lazy=True))  # Add relationship to Course

