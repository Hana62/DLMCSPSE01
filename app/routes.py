from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask import current_app as app, jsonify
from . import db, bcrypt
from datetime import datetime, date
import random
from .models import User, Course, UserCourse, Exam, Question, Answer, ExamQuestion, ExamBooking, Response, Evaluation
from flask import flash, redirect, url_for, render_template, request


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
    return render_template('login.html')


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



@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email_address=email).first()  # Use email_address field to find user
        if user:
            # Here you would implement the logic to send a password reset email
            # e.g., send_password_reset_email(user)
            flash('An email with password reset instructions has been sent.', 'info')
            return redirect(url_for('login'))  # Redirect back to login page
        else:
            flash('No account associated with this email.', 'danger')

    return render_template('forgot_password.html')  # Create this template

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

    # Collect statistics for each exam, including course name
    exam_stats = []
    for exam in exams:
        registered_students_count = ExamBooking.query.filter_by(exam_id=exam.id).count()
        students_taken_exam = Evaluation.query.filter_by(exam_id=exam.id).count()
        students_passed_exam = Evaluation.query.filter_by(exam_id=exam.id, pass_or_fail=True).count()

        # Fetch the course associated with the exam
        course = Course.query.get(exam.course_id)

        exam_stats.append({
            'exam': exam,
            'course_name': course.name if course else "N/A",  # Include course name here
            'registered_count': registered_students_count,
            'taken_count': students_taken_exam,
            'passed_count': students_passed_exam
        })

    return render_template('teacher_panel.html', courses=courses, exams=exams, exam_stats=exam_stats)

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


@app.route('/teacher_panel/results/<int:exam_id>')
@login_required
def view_results(exam_id):
    if current_user.role != 'Teacher':
        flash('Access Denied', 'danger')
        return redirect(url_for('index'))

    # Fetch the exam details
    exam = Exam.query.filter_by(id=exam_id).first()
    if not exam:
        flash('Exam not found.', 'danger')
        return redirect(url_for('teacher_panel'))

    # Fetch evaluation results with user and exam details included
    results = (
        Evaluation.query
        .filter_by(exam_id=exam_id)
        .join(User, Evaluation.user_id == User.id)
        .add_columns(User.first_name, User.last_name, User.email_address, Evaluation.grade, Evaluation.pass_or_fail, Evaluation.submission_date)
        .all()
    )

    return render_template('view_results.html', results=results, exam=exam)
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


@app.route('/student_panel')
@login_required
def student_panel():
    # Show a simple student dashboard
    return render_template('student_panel.html')


@app.route('/student/courses', methods=['GET'])
@login_required
def available_courses():
    if current_user.role != 'Student':
        flash('Access Denied', 'danger')
        return redirect(url_for('index'))

    # Fetch courses with at least one upcoming exam
    upcoming_exams = db.session.query(Course).join(Exam).filter(Exam.date_scheduled >= date.today()).all()

    # Fetch the student's registered courses
    registered_course_ids = db.session.query(UserCourse.course_id).filter(UserCourse.user_id == current_user.id).all()
    registered_course_ids = [course_id for (course_id,) in registered_course_ids]  # Unpack the result into a list

    return render_template('student_courses.html', courses=upcoming_exams, registered_course_ids=registered_course_ids)

@app.route('/student/register_course/<int:course_id>', methods=['POST'])
@login_required
def register_course(course_id):
    if current_user.role != 'Student':
        flash('Access Denied', 'danger')
        return redirect(url_for('index'))

    # Check if the student is already registered for the course
    existing_registration = UserCourse.query.filter_by(user_id=current_user.id, course_id=course_id).first()

    if existing_registration:
        flash('You are already registered for this course.', 'info')
    else:
        # Register the student for the course
        new_registration = UserCourse(user_id=current_user.id, course_id=course_id)
        db.session.add(new_registration)
        db.session.commit()
        flash('You have been successfully registered for the course.', 'success')

    return redirect(url_for('available_courses'))



@app.route('/student/my_courses', methods=['GET'])
@login_required
def my_courses():
    if current_user.role != 'Student':
        flash('Access Denied', 'danger')
        return redirect(url_for('index'))

    # Get the student's registered courses
    registered_courses = db.session.query(Course).join(UserCourse).filter(UserCourse.user_id == current_user.id).all()

    # Fetch upcoming exams for those courses
    upcoming_exams = {}
    booked_exams = set()
    exam_countdowns = {}
    completed_exams = set()  # Track exams that have been completed

    for course in registered_courses:
        exams = Exam.query.filter(Exam.course_id == course.id, Exam.date_scheduled >= date.today()).all()
        upcoming_exams[course.id] = exams

        for exam in exams:
            # Check if there's an evaluation for this exam by the current student
            evaluation = Evaluation.query.filter_by(user_id=current_user.id, exam_id=exam.id).first()
            if evaluation:
                # Mark as completed if evaluation exists
                completed_exams.add(exam.id)
                continue  # Skip further checks if exam is already taken

            # Fetch booked exams for the current student
            booking = ExamBooking.query.filter_by(user_id=current_user.id, exam_id=exam.id).first()
            if booking:
                booked_exams.add(exam.id)

                # Calculate countdown
                time_remaining = exam.date_scheduled - datetime.now()
                exam_countdowns[exam.id] = time_remaining

    return render_template(
        'student_my_courses.html',
        courses=registered_courses,
        upcoming_exams=upcoming_exams,
        booked_exams=booked_exams,
        exam_countdowns=exam_countdowns,
        completed_exams=completed_exams  # Pass completed exams to the template
    )


@app.route('/student/book_exam/<int:exam_id>', methods=['POST'])
@login_required
def book_exam(exam_id):
    # Fetch the exam from the database
    exam = Exam.query.get_or_404(exam_id)

    # Check if the current user is a student
    if current_user.role != 'Student':
        flash("Only students can book exams.", "danger")
        return redirect(url_for('index'))

    # Check if the student is enrolled in the course related to the exam
    user_course = UserCourse.query.filter_by(user_id=current_user.id, course_id=exam.course_id).first()
    if not user_course:
        flash("You are not enrolled in this course and cannot book the exam.", "danger")
        return redirect(url_for('student_panel'))

    # Check if the exam is in the past or already started
    if datetime.strftime(exam.date_scheduled, '%Y-%m-%d') < datetime.strftime(date.today(), '%Y-%m-%d'):
        flash("This exam has already started or is in the past.", "danger")
        return redirect(url_for('student_panel'))

    # Check if the student has already booked this exam
    existing_booking = ExamBooking.query.filter_by(user_id=current_user.id, exam_id=exam_id).first()
    if existing_booking:
        flash("You have already booked this exam.", "danger")
        return redirect(url_for('student_panel'))

    # Check if there is enough capacity (optional)
    max_capacity = 50  # Example, if you have capacity logic
    current_bookings = ExamBooking.query.filter_by(exam_id=exam_id).count()
    if current_bookings >= max_capacity:
        flash("This exam is fully booked.", "danger")
        return redirect(url_for('student_panel'))

    # Create a new exam booking
    booking = ExamBooking(user_id=current_user.id, exam_id=exam_id)
    db.session.add(booking)
    db.session.commit()

    # Send email confirmation (optional)
    # send_exam_confirmation_email(current_user.email_address, exam)

    flash("You have successfully booked the exam!", "success")
    return redirect(url_for('student_panel'))








@app.route('/take_exam/<int:exam_id>', methods=['GET', 'POST'])
@login_required
def take_exam(exam_id):
    # Check if the user is registered for the course of this exam
    exam = Exam.query.get_or_404(exam_id)
    course_id = exam.course_id

    # Ensure the user is registered for the course
    is_registered = UserCourse.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    if not is_registered:
        flash("You are not registered for any courses.")
        return redirect(url_for('student_dashboard'))

    # Get the questions for the exam
    exam_questions = ExamQuestion.query.filter_by(exam_id=exam_id).all()

    # Retrieve the question details for each exam question
    questions = []
    for exam_question in exam_questions:
        question = Question.query.get(exam_question.question_id)
        if question:
            questions.append(question)

    # Pass duration in seconds
    duration_seconds = exam.duration * 60

    return render_template('take_exam.html', exam=exam, questions=questions, exam_duration=duration_seconds)



@app.route('/submit_exam/<int:exam_id>', methods=['POST'])
@login_required
def submit_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    exam_questions = ExamQuestion.query.filter_by(exam_id=exam_id).all()

    correct_count = 0
    total_questions = len(exam_questions)

    # Process each question and user's answer
    for exam_question in exam_questions:
        question_id = exam_question.question_id
        user_answer = request.form.get(f'question_{question_id}')

        # Check if the answer is correct
        if user_answer:
            # Save the user's response
            response = Response(
                exam_id=exam.id,
                user_id=current_user.id,
                question_id=question_id,
                response=user_answer
            )
            db.session.add(response)

            # Check if the user's answer is correct
            correct_answer = Answer.query.filter_by(question_id=question_id, is_correct=True).first()
            if correct_answer and user_answer == str(correct_answer.id):  # Compare the user's answer ID with the correct one
                correct_count += 1

    db.session.commit()

    # Calculate the grade
    grade = (correct_count / total_questions) * 100 if total_questions > 0 else 0
    passed = grade >= exam.passing_grade

    # Store the evaluation with submission date
    evaluation = Evaluation(
        user_id=current_user.id,
        exam_id=exam.id,
        course_id=exam.course_id,
        answered_count=total_questions,
        corrected_count=correct_count,
        grade=grade,
        pass_or_fail=passed,
        submission_date=datetime.utcnow()  # Set the current date and time as submission_date
    )
    db.session.add(evaluation)
    db.session.commit()

    flash(f"Your exam has been submitted successfully. Grade: {grade:.2f}%.", "success")
    return redirect(url_for('student_panel'))


@app.route('/exam_results')
@login_required
def exam_results():
    # Fetch evaluations for the current user and join related tables
    evaluations = db.session.query(
        Evaluation,
        Exam.title,
        Exam.date_scheduled,
        ExamBooking.booking_date
    ).join(Exam, Evaluation.exam_id == Exam.id) \
     .join(ExamBooking, (Evaluation.exam_id == ExamBooking.exam_id) & (Evaluation.user_id == ExamBooking.user_id)) \
     .filter(Evaluation.user_id == current_user.id).all()

    return render_template('exam_results.html', evaluations=evaluations)


@app.route('/exam_questions_answers/<int:exam_id>', methods=['GET'])
@login_required
def exam_questions_answers(exam_id):
    exam_questions = ExamQuestion.query.filter_by(exam_id=exam_id).all()
    questions_data = []

    for exam_question in exam_questions:
        question = Question.query.get(exam_question.question_id)
        user_response = Response.query.filter_by(
            exam_id=exam_id,
            user_id=current_user.id,
            question_id=question.id
        ).first()

        # Gather all answers for this question
        answers = [{'answer_text': answer.answer_text,
                    'is_correct': answer.is_correct,
                    'is_selected': user_response.response == answer.id if user_response else False,
                    'answer_id': answer.id}  # Store the answer ID for comparison
                   for answer in question.answers]

        questions_data.append({
            'question_text': question.question_text,
            'id': question.id,  # Store question id to use in the front-end
            'answers': answers,
            'selected_answer_id': user_response.response if user_response else None  # Store the selected answer ID
        })

    return jsonify({'questions': questions_data})