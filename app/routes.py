from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask import current_app as app
from flask import render_template, request, redirect, url_for, flash
from .models import User, Course, Exam, Question, Answer, Evaluation, ExamQuestion
from . import db, bcrypt
from datetime import datetime

import random
from flask import render_template, request, redirect, url_for, flash
from .models import User, Course, Exam, Question, Answer, ExamQuestion
from . import db
from flask_login import login_required, current_user

# Ensure imports are not duplicated
from werkzeug.security import check_password_hash


@app.route('/login', methods=['GET', 'POST'])
def login():
    print("Login route accessed")  # Debug statement
    if request.method == 'POST':
        print("POST request detected")  # Debug statement
        username = request.form.get('username')
        password = request.form.get('password')

        # Fetch user from the database
        user = User.query.filter_by(username=username).first()

        # Check if user exists and password is correct
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)  # Log the user in
            flash("Login successful!")

            # Redirect based on user role
            if user.role == 'Teacher':
                return redirect(url_for('teacher_panel'))  # Teacher panel route
            else:
                return redirect(url_for('student_panel'))  # Student panel route
        else:
            flash("Invalid username or password.")
            return render_template('login.html')  # Return to login page with error

    # Render the login page for GET request
    return render_template('login.html')  # Make sure to always return the template for GET requests


@app.route('/logout')
@login_required
def logout():
    logout_user()  # Log the user out
    flash("Logout successful!")
    return redirect(url_for('login'))  # Redirect to login page


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        role = request.form.get('role')  # Capture the role ("Student" or "Teacher")

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            password=hashed_password,
            email_address=email,
            role=role  # Save the selected role
        )

        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful!")
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'Teacher':  # Assuming role is used consistently here
        return redirect(url_for('index'))
    # Admin panel logic
    return render_template('admin.html')


@app.route('/add_question/<int:course_id>', methods=['GET', 'POST'])
@login_required
def add_question(course_id):
    if request.method == 'POST':
        try:
            # Get the form data
            question_text = request.form['question_text']
            difficulty = request.form['difficulty']

            # Create a new Question
            new_question = Question(
                question_text=question_text,
                difficulty=difficulty,
                course_id=course_id,
                added_by=current_user.id
            )
            db.session.add(new_question)
            db.session.flush()  # Flush the session to get the question ID for answers

            # Get the answers from the form
            answer1 = request.form['answer1']
            answer2 = request.form['answer2']
            answer3 = request.form['answer3']
            answer4 = request.form['answer4']
            correct_answer = int(request.form['correct_answer'])  # Correct answer is provided as 1-4

            # Add answers to the database, marking the correct one
            answers = [
                Answer(answer_text=answer1, question_id=new_question.id, is_correct=(correct_answer == 1)),
                Answer(answer_text=answer2, question_id=new_question.id, is_correct=(correct_answer == 2)),
                Answer(answer_text=answer3, question_id=new_question.id, is_correct=(correct_answer == 3)),
                Answer(answer_text=answer4, question_id=new_question.id, is_correct=(correct_answer == 4))
            ]
            db.session.add_all(answers)
            db.session.commit()

            flash('Question and answers added successfully!')
            return redirect(url_for('manage_questions', course_id=course_id))

        except KeyError as e:
            flash(f"Missing form field: {str(e)}")
            return render_template('add_question.html', course_id=course_id)

    return render_template('add_question.html', course_id=course_id)
    # return redirect(url_for('manage_questions', course_id=question.course_id))


@app.route('/manage_courses')
@login_required
def manage_courses():
    if current_user.role != 'Teacher':
        flash("You are not authorized to view this page!")
        return redirect(url_for('index'))

    courses = Course.query.filter_by(teacher_id=current_user.id).all()
    return render_template('manage_courses.html', courses=courses)



@app.route('/manage_questions/<int:course_id>', methods=['GET'])
@login_required
def manage_questions(course_id):
    # Ensure the current user is a teacher or has permissions
    if current_user.role != 'Teacher':
        flash('You do not have permission to manage questions.')
        return redirect(url_for('index'))

    # Fetch all questions for the given course, along with their answers
    questions = Question.query.filter_by(course_id=course_id).all()

    # Pass course_id to the template
    return render_template('manage_questions.html', questions=questions, course_id=course_id)



@app.route('/edit_question/<int:question_id>', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    # Get the question from the database
    question = Question.query.get_or_404(question_id)

    # Ensure the current user is a teacher and owns the question
    if current_user.role != 'Teacher':
        flash('You do not have permission to edit this question.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            # Update the question text and difficulty
            question.question_text = request.form['question_text']
            question.difficulty = request.form['difficulty']

            # Update the answers
            question.answers[0].answer_text = request.form['answer1']
            question.answers[1].answer_text = request.form['answer2']
            question.answers[2].answer_text = request.form['answer3']
            question.answers[3].answer_text = request.form['answer4']

            # Update the correct answer
            correct_answer = int(request.form['correct_answer'])
            for i, answer in enumerate(question.answers):
                answer.is_correct = (i + 1 == correct_answer)

            db.session.commit()
            flash('Question updated successfully!')
            return redirect(url_for('manage_questions', course_id=question.course_id))

        except KeyError as e:
            flash(f"Missing form field: {str(e)}")

    return render_template('edit_question.html', question=question)


@app.route('/delete_question/<int:question_id>', methods=['POST'])
@login_required
def delete_question(question_id):
    # Ensure the current user is a teacher or has permissions
    if current_user.role != 'Teacher':
        flash('You do not have permission to delete questions.')
        return redirect(url_for('index'))

    # Find the question by ID
    question = Question.query.get_or_404(question_id)

    # Delete the question and all its associated answers
    db.session.delete(question)
    db.session.commit()

    flash('Question and its answers have been deleted successfully.')
    return redirect(url_for('manage_questions', course_id=question.course_id))



@app.route('/take_exam/<int:exam_id>', methods=['GET', 'POST'])
@login_required
def take_exam(exam_id):
    # Student taking exam logic
    pass


@app.route('/grade_exam/<int:exam_id>', methods=['POST'])
@login_required
def grade_exam(exam_id):
    # Grade the exam logic
    pass


@app.route('/results/<int:exam_id>')
@login_required
def results(exam_id):
    # Show exam results logic
    pass


@app.route('/student_panel')
@login_required  # Ensure this route is protected for logged-in users
def student_panel():
    return render_template('student_panel.html')  # Ensure template exists


# @app.route('/teacher_panel')
# @login_required
# def teacher_panel():
#     # Assuming you have a Course model and you want to show all courses
#     courses = Course.query.all()  # Fetch courses from the database
#     return render_template('teacher_panel.html', courses=courses)  # Pass the courses to the template
#


# Ensure the app is initialized in __init__.py or app.py
login_manager = LoginManager()
login_manager.init_app(app)


# User loader function
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/add_course', methods=['GET', 'POST'])
@login_required
def add_course():
    if current_user.role != 'Teacher':
        flash("You are not authorized to add courses!")
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']

        new_course = Course(
            name=name,
            description=description,
            teacher_id=current_user.id  # Link to the teacher
        )

        db.session.add(new_course)
        db.session.commit()
        flash("Course added successfully!")
        return redirect(url_for('teacher_panel'))

    return render_template('add_course.html')



# Teacher Dashboard Route
@app.route('/teacher_panel')
@login_required
def teacher_panel():
    # Ensure the logged-in user is a teacher
    if current_user.role != 'Teacher':
        flash('Access Denied: You must be a teacher to access this page.', 'danger')
        return redirect(url_for('index'))

    # Query courses, exams, and results related to the teacher
    courses = Course.query.filter_by(teacher_id=current_user.id).all()
    exams = Exam.query.filter_by(created_by=current_user.id).all()
    results = Evaluation.query.filter_by(course_id=current_user.id).all()  # Student evaluations

    return render_template('teacher_panel.html', courses=courses, exams=exams, results=results)


# View all Courses of the teacher
@app.route('/teacher_panel/courses')
@login_required
def view_courses():
    if current_user.role != 'Teacher':
        flash('Access Denied', 'danger')
        return redirect(url_for('index'))

    courses = Course.query.filter_by(teacher_id=current_user.id).all()
    return render_template('view_courses.html', courses=courses)


# Manage exams related to a specific course
@app.route('/teacher_panel/exams/<int:course_id>')
@login_required
def manage_exams(course_id):
    # Fetch the course by course_id to ensure it exists
    course = Course.query.get(course_id)

    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for('teacher_panel'))

    # Fetch all exams for the specific course
    exams = Exam.query.filter_by(course_id=course_id).all()

    # Pass exams and course_id to the template
    return render_template('manage_exams.html', exams=exams, course_id=course_id, course_title=course.name)

@app.route('/teacher_panel/edit_exam/<int:exam_id>', methods=['GET', 'POST'])
@login_required
def edit_exam(exam_id):
    # Logic to edit the exam
    exam = Exam.query.get(exam_id)
    if request.method == 'POST':
        # Handle the form submission to edit the exam
        pass
    return render_template('edit_exam.html', exam=exam)

@app.route('/teacher_panel/delete_exam/<int:exam_id>', methods=['POST'])
@login_required
def delete_exam(exam_id):
    # Logic to delete the exam
    exam = Exam.query.get(exam_id)
    if exam:
        db.session.delete(exam)
        db.session.commit()
        flash("Exam deleted successfully!", "success")
    else:
        flash("Exam not found.", "danger")
    return redirect(url_for('manage_exams', course_id=exam.course_id))

# Route to manage exams
# @app.route('/teacher_panel/manage_exams', methods=['GET'])
# def manage_exams():
#     exams = Exam.query.all()
#     return render_template('manage_exams.html', exams=exams)

# New route to view questions for a specific exam
@app.route('/teacher_panel/exam_questions/<int:exam_id>', methods=['GET'])
@login_required
def exam_questions(exam_id):
    exam = Exam.query.get_or_404(exam_id)  # Fetch the exam by ID
    questions = ExamQuestion.query.filter_by(exam_id=exam_id).all()  # Get questions for the exam

    question_data = []  # To store structured question data
    for eq in questions:
        question = Question.query.get(eq.question_id)  # Fetch the question
        answers = Answer.query.filter_by(question_id=question.id).all()  # Fetch answers for each question
        question_data.append({
            'question_text': question.question_text,  # Use question.question_text
            'answers': answers,
            'correct_answer': next((answer for answer in answers if answer.is_correct), None),  # Get the correct answer object
            'difficulty': question.difficulty  # Use question.difficulty
        })

    return render_template('exam_questions.html', exam=exam, question_data=question_data)

# Manage questions related to a specific exam
@app.route('/teacher_panel/questions/<int:exam_id>')
@login_required
def manage_exam_questions(exam_id):
    if current_user.role != 'Teacher':
        flash('Access Denied', 'danger')
        return redirect(url_for('index'))

    questions = Question.query.filter_by(exam_id=exam_id).all()
    return render_template('manage_exam_questions.html', questions=questions)


# View student results for an exam
@app.route('/teacher_panel/results/<int:exam_id>')
@login_required
def view_results(exam_id):
    if current_user.role != 'Teacher':
        flash('Access Denied', 'danger')
        return redirect(url_for('index'))

    results = Evaluation.query.filter_by(exam_id=exam_id).all()
    return render_template('view_results.html', results=results)

# Route to create an exam
# Route to create an exam
@app.route('/teacher_panel/create_exam/<int:course_id>', methods=['GET', 'POST'])
@login_required
def create_exam(course_id):
    if current_user.role != 'Teacher':
        flash("You are not authorized to create exams!")
        return redirect(url_for('index'))

    course = Course.query.get_or_404(course_id)

    if request.method == 'POST':
        title = request.form.get('title')
        number_of_questions = int(request.form.get('number_of_questions'))
        passing_grade = int(request.form.get('passing_grade'))
        date_scheduled = request.form.get('date_scheduled')
        duration = int(request.form.get('duration'))
        try:
            date_scheduled = datetime.strptime(date_scheduled, '%Y-%m-%d')  # Assuming format is 'YYYY-MM-DD'
        except ValueError:
            flash("Invalid date format. Please enter a valid date in 'YYYY-MM-DD' format.")
            return render_template('create_exam.html')
        # Create the new exam
        new_exam = Exam(
            title=title,
            course_id=course.id,
            number_of_questions=number_of_questions,
            passing_grade=passing_grade,
            created_by=current_user.id,
            date_scheduled=date_scheduled,
            duration=duration
        )

        db.session.add(new_exam)
        db.session.flush()  # Flush to get the exam ID for exam questions

        # Fetch random questions for the course
        questions = Question.query.filter_by(course_id=course_id).all()

        if len(questions) < number_of_questions:
            flash("Not enough questions in the course to create the exam.")
            return render_template('create_exam.html', course=course)

        selected_questions = random.sample(questions, number_of_questions)

        # Add selected questions to the ExamQuestion table
        for question in selected_questions:
            exam_question = ExamQuestion(
                exam_id=new_exam.id,
                course_id=course.id,
                question_id=question.id
            )
            db.session.add(exam_question)

        db.session.commit()
        flash("Exam created successfully!")
        return redirect(url_for('manage_exams', course_id=course.id))

    return render_template('create_exam.html', course=course)

