from datetime import date

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship
from twilio.rest import Client
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user


import sqlite3


app = Flask(__name__)

# create the extension
db = SQLAlchemy()

# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tkiet_attendance.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# initialize the app with the extension
db.init_app(app)
app.app_context().push()

defaulterStudent = []


app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
# Creating the Student Table


class Student_info(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    PRN = db.Column(db.String(12), unique=True)
    name = db.Column(db.String(80))
    password = db.Column(db.String(20))
    email = db.Column(db.String(30))
    roll_no = db.Column(db.Integer)
    phone_no = db.Column(db.Integer)
    depart_name = db.Column(db.String(30))
    year = db.Column(db.String(20))
    division = db.Column(db.String(2))
    userPosition = db.Column(db.String(10))
    # attendances = relationship("StudentAttendance", back_populates="attendance")


class StudentAttendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    studentPRN = db.Column(db.String(12))
    date = db.Column(db.String(50))
    subject = db.Column(db.String(30))
    depart_name = db.Column(db.String(30))
    year = db.Column(db.String(20))
    division = db.Column(db.String(2))
    UniqueConstraint(studentPRN, date, subject)


class AdminDatabase(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(30))
    name = db.Column(db.String(40))
    position = db.Column(db.String(40))


class Leaves(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prn = db.Column(db.String(30))
    # name = db.Column(db.String(30))
    # rollNo = db.Column(db.String(10))
    # department = db.Column(db.String(30))
    # division = db.Column(db.String(30))
    # year = db.Column(db.String(20))
    description = db.Column(db.String(50))
    date = db.Column(db.String(10))
    status = db.Column(db.String(20))


db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return Student_info.query.get(int(user_id))


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username')

        password = request.form.get('password')
        get_user = Student_info.query.filter_by(PRN=username).first()
        if not get_user:
            flash("invalid username")
            print("user Not Exist")
        elif get_user.password != password:
            flash("Invalid Password")

            print("Invalid Password")
        else:
            print("login")
            login_user(get_user)
            return redirect(url_for('home'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/student_information")
def student_information():
    all_student_info = Student_info.query.all()
    return render_template('student.html', all_students=all_student_info, info_lenth=len(all_student_info), count=0)


@app.route("/add_student", methods=['POST', 'GET'])
def add_student():

    # Getting the student information from the website form
    if request.method == "POST":
        prn = request.form.get('prn')
        name = request.form.get('name')
        roll_no = request.form.get('roll_no')
        email = request.form.get('email')
        phone_no = request.form.get('phone_no')
        depart_name = request.form.get('Department')
        year = request.form.get('Year')
        division = request.form.get('Division')
        # print(depart_name, year, division)
        # Adding new Student Data To the Database
        new_student = Student_info(
            PRN=prn,
            name=name,
            roll_no=roll_no,
            email=email,
            password="tkiet@123",
            phone_no=phone_no,
            depart_name=depart_name,
            year=year,
            division=division,
            userPosition="student"
        )
        db.session.add(new_student)
        db.session.commit()
        return redirect(url_for('student_information'))
    return render_template('student_add.html')


@app.route("/take_attendance", methods=['GET', 'POST'])
def takeAttendace():
    all_student_info = Student_info.query.all()
    present_students = []

    if request.method=='POST':
        subject = request.form.get('subject')
        for student in all_student_info:
            if request.form.get(student.PRN) == "on":
                present_students.append(student)
        print(present_students)

        # Adding the information of attendance to the database
        for present in present_students:
            new_attendance = StudentAttendance(
                studentPRN=present.PRN,
                subject=subject,
                date=date.today().strftime("%B %d, %Y"),
                depart_name=present.depart_name,
                year=present.year,
                division=present.division
            )
            db.session.add(new_attendance)
            db.session.commit()

    return render_template('take_attendance.html', students=all_student_info)


@app.route("/take_attendance1", methods=['GET', 'POST'])
def departmentviseStudentAttendance():
    all_student_info = Student_info.query.all()
    takeAttendaceStudents = []
    if request.method == 'POST':
        depart_name = request.form.get('Department')
        year = request.form.get('Year')
        division = request.form.get('Division')
        for student in all_student_info:
            if student.depart_name == depart_name and student.year == year and student.division == division:
                takeAttendaceStudents.append(student)
        print(depart_name, division, year)
        return render_template('take_attendance.html', students=takeAttendaceStudents)


@app.route("/view_attendance1", methods=['GET', 'POST'])
def departmentviseStudentView():
    all_attendance = StudentAttendance.query.all()
    viewAttendaceStudents = []
    conductedLechture={}
    conductedDate=[]
    studentSubjectAttendance = {}
    subjects = []
    totalLecatures = 0
    presentStudentPrns = []
    if request.method == 'POST':
        depart_name = request.form.get('Department')
        year = request.form.get('Year')
        division = request.form.get('Division')
        print(depart_name, year, division)
        for student in all_attendance:
            if student.depart_name == depart_name and student.year == year and student.division == division:
                viewAttendaceStudents.append(student)
                if student.subject not in subjects:
                    subjects.append(student.subject)
                if student.subject not in conductedLechture.keys():
                    conductedLechture[student.subject] = 1
                    totalLecatures+=1
                    conductedDate.append(student.date)
                elif student.date not in conductedDate:
                    totalLecatures+=1
                    conductedLechture[student.subject] += 1

        count=0
        for presentStudent in viewAttendaceStudents:
            if presentStudent.studentPRN not in studentSubjectAttendance.keys():
                studentSubjectAttendance[presentStudent.studentPRN] = {}
                presentStudentPrns.append(presentStudent.studentPRN)

            for subject in subjects:
                if subject not in studentSubjectAttendance[presentStudent.studentPRN].keys():
                    studentSubjectAttendance[presentStudent.studentPRN][subject]=0
            for subject in subjects:
                if subject == presentStudent.subject:
                    count += 1
                    studentSubjectAttendance[presentStudent.studentPRN][subject]+=1


        for PrnOfStudets in presentStudentPrns:
            total = 0
            for subject in subjects:
                total += studentSubjectAttendance[PrnOfStudets][subject]
            studentSubjectAttendance[PrnOfStudets]['total']=total
        # print(count)
        # print(viewAttendaceStudents)
        print(conductedLechture)
        # print(subjects)
        print(studentSubjectAttendance)
        print(presentStudentPrns)
        print(totalLecatures)
        return render_template('view_attendance.html', students=studentSubjectAttendance, subjects=conductedLechture.keys(), no_of_records=len(viewAttendaceStudents), conductedLechture=conductedLechture, presentStudent=studentSubjectAttendance.keys())


@app.route("/view_attendance", methods=['GET', 'POST'])
def view_attendance():
    if request.method == "POST":
        prn_of_student = request.form.get('view_prn')
        student = Student_info.query.get(prn_of_student)
        student_presenti = StudentAttendance.query.all()
        total_attendance=0
        for present_record in student_presenti:
            if present_record.studentPRN == prn_of_student:
                total_attendance += 1

        return render_template("view_attendance.html", students=student_presenti, prn_of_student=prn_of_student, no_of_records=len(student_presenti), prensent_student_data=student, total_attendance=total_attendance)
    return render_template('view_attendance.html', prensent_student_data=None)


AttendancePercentage = {}
@app.route('/sendMessage', methods=['GET','POST'])
def sendMessage():
    all_attendance = StudentAttendance.query.all()
    viewAttendaceStudents = []
    conductedLechture = {}
    conductedDate = []
    studentSubjectAttendance = {}
    subjects = []
    totalLecatures = 0
    presentStudentPrns = []
    global AttendancePercentage
    AttendancePercentage = {}

    if request.method == 'POST':
        depart_name = request.form.get('Department')
        year = request.form.get('Year')
        division = request.form.get('Division')
        print(depart_name, year, division)
        for student in all_attendance:
            if student.depart_name == depart_name and student.year == year and student.division == division:
                viewAttendaceStudents.append(student)
                if student.subject not in subjects:
                    subjects.append(student.subject)
                if student.subject not in conductedLechture.keys():
                    conductedLechture[student.subject] = 1
                    totalLecatures += 1
                    conductedDate.append(student.date)
                elif student.date not in conductedDate:
                    totalLecatures += 1
                    conductedLechture[student.subject] += 1

        count = 0
        for presentStudent in viewAttendaceStudents:
            if presentStudent.studentPRN not in studentSubjectAttendance.keys():
                studentSubjectAttendance[presentStudent.studentPRN] = {}
                presentStudentPrns.append(presentStudent.studentPRN)

            for subject in subjects:
                if subject not in studentSubjectAttendance[presentStudent.studentPRN].keys():
                    studentSubjectAttendance[presentStudent.studentPRN][subject] = 0
            for subject in subjects:
                if subject == presentStudent.subject:
                    count += 1
                    studentSubjectAttendance[presentStudent.studentPRN][subject] += 1

        for PrnOfStudets in presentStudentPrns:
            total = 0
            for subject in subjects:
                total += studentSubjectAttendance[PrnOfStudets][subject]
                AttendancePercentage[PrnOfStudets] = (total/totalLecatures)*100
            studentSubjectAttendance[PrnOfStudets]['total'] = total
        # print(count)
        # print(viewAttendaceStudents)
        print(conductedLechture)
        # print(subjects)
        print(studentSubjectAttendance)
        print(presentStudentPrns)
        print(totalLecatures)
        print(AttendancePercentage)
        return render_template('sendMessage.html', percentage=AttendancePercentage, studentsPrn=AttendancePercentage.keys(), all_student_info=Student_info.query.all())
    return render_template('SendMessage.html', percentage="", studentsPrn="", all_student_info="")




@app.route('/applyleave', methods=['POST', 'GET'])
def applyLeave():
    if request.method == 'POST':
        newLeave = Leaves(
            prn=current_user.PRN,
            date=date.today().strftime("%B %d, %Y"),
            description=request.form.get('Reason'),
            status="PENDING"
        )
        db.session.add(newLeave)
        db.session.commit()
    return render_template('applyLeave.html')


@app.route('/viewLeaves', methods=['POST', 'GET'])
def viewLeaves():
    allLeaves = Leaves.query.all()
    allStuents = Student_info.query.all()
    if request.method == 'POST':
        leaveid = request.form.get('value')
        print(leaveid)
        applier = Leaves.query.filter_by(id=leaveid).first()
        print(applier)
        applier.status="Approve"
        db.session.commit()
        return redirect(url_for('viewLeaves'))
    return  render_template('viewLeaves.html', allLeaves=allLeaves, students=allStuents)


@app.route('/studentLeaves', methods=['POST','GET'])
def studentLeaves():
    userLeave = Leaves.query.filter_by(prn=current_user.PRN).all()
    return render_template("studentLeave.html", userLeaves=userLeave)
if __name__ == '__main__':
    app.run(debug=True)