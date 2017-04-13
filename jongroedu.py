from flask import Flask, flash, redirect, render_template, url_for, request, jsonify
from flaskext.mysql import MySQL
import sys, datetime
from passlib.hash import bcrypt

reload(sys)
sys.setdefaultencoding('utf-8')

app = Flask(__name__)
mysql = MySQL()

app.secret_key = 'jongroeinsacademyqingdaochina'
app.config['MYSQL_DATABASE_USER'] = 'website'
app.config['MYSQL_DATABASE_PASSWORD'] = '0905aebin'
app.config['MYSQL_DATABASE_DB'] = 'academy'
app.config['MYSQL_DATABASE_HOST'] = '117.52.89.194'

mysql.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['Username']
        password = request.form['Password']
        cursor = (mysql.connect()).cursor()
        username_check_sql = "SELECT EXISTS(SELECT 1 FROM user WHERE ID = '{0}');".format(username)
        cursor.execute(username_check_sql)
        username_check_result = cursor.fetchone()[0]
        if username_check_result == 1:
            get_password_sql = "SELECT PW FROM user WHERE ID = '{0}';".format(username)
            cursor.execute(get_password_sql)
            get_password_result = cursor.fetchone()[0]
            if bcrypt.verify(password, get_password_result):
                flash("Login successful")
                ### user type: 0: admin, 1: teacher, 2: student, 3: parent
                get_user_type_sql = "SELECT type FROM user WHERE ID = '{0}';".format(username)
                cursor.execute(get_user_type_sql)
                user_type_result = cursor.fetchone()[0]
                if user_type_result == 0:
                    ### user is admin
                    return redirect(url_for('datalist'))
                elif user_type_result == 2:
                    ### user is student
                    get_student_id_sql = "SELECT uniqueID FROM user WHERE ID = '{0}';".format(username)
                    cursor.execute(get_student_id_sql)
                    student_id_result = cursor.fetchone()[0]
                    return redirect(url_for('student_profile', studentid=student_id_result))
                elif (user_type_result == 1) or (user_type_result == 3):
                    ### if user is teacher, or parent we redirect that user to preparing page
                    return redirect(url_for('preparing'))
            else:
                flash("Invalid Credentials. Please try again")
        else:
            flash("Invalid Username or Password. Please try again")
    return render_template('login.html')

@app.route('/datalist')
def datalist():
    cursor = (mysql.connect()).cursor()
    get_data_lists_sql = "SELECT * FROM student;"
    cursor.execute(get_data_lists_sql)
    data_lists = cursor.fetchall()
    return render_template('datalist.html', data_lists=data_lists)

@app.route('/_change_db')
def change_db():
    db_name = request.args.get('db_name', type=str)
    cursor = (mysql.connect()).cursor()
    if db_name == "class":
        get_data_lists_sql = "SELECT c.uniqueID, c.name, t.name, c.startDate, c.endDate, c.startTime, c.endTime, c.dayOfWeek, c.book, cg.name FROM class c, teacher t, classGroup cg WHERE (c.groupID = cg.ID) AND (c.teacherUID = t.UUID);"
    else:
        get_data_lists_sql = "SELECT * FROM {0};".format(db_name)
    cursor.execute(get_data_lists_sql)
    data_lists = cursor.fetchall()
    if db_name == "student":
        keys = ['Student ID', 'Name', 'Date of Birth', 'Phone Number', 'Address', 'School', 'Grade']
    elif db_name == "teacher":
        keys = ['Teacher ID', 'Name', 'Date of Birth', 'Phone Number', 'Address']
    elif db_name == "class":
        keys = ['Class ID', 'Name', 'Teacher', 'Start Date', 'End Date', 'Start Time', 'End Time', 'Day of Week', 'Textbook', 'Group Name']
    elif db_name == "parent":
        keys = ['Parent ID', 'Name', 'Date of Birth', 'Phone Number', 'Address']
    return jsonify(db_name=db_name, columns=keys, rows=data_lists)

@app.route('/student/<studentid>')
def student_profile(studentid):
    cursor = (mysql.connect()).cursor()
    # student profile
    get_data_sql = "SELECT * FROM student WHERE UUID = {0};".format(studentid)
    cursor.execute(get_data_sql)
    data = cursor.fetchone()
    # student class data
    today = datetime.datetime.now()
    today_date = today.strftime("%Y-%m-%d")
    student_condition = "(cs.studentUID = '{0}')".format(studentid)
    class_base_sql = "SELECT cg.name, c.name, t.name FROM classGroup cg, class c, teacher t, classStudent cs WHERE (cg.ID = c.groupID) AND (c.teacherUID = t.UUID) AND (c.uniqueID = cs.classUID) AND {0}".format(student_condition)
    current_condition_sql = "(date('{0}') BETWEEN c.startDate AND c.endDate)".format(today_date, str(today.weekday()))
    history_condition_sql = "NOT(" + current_condition_sql + ")"
    class_current_sql =  class_base_sql + "  AND {0};".format(current_condition_sql)
    class_history_sql =  class_base_sql + " AND {0};".format(history_condition_sql)
    cursor.execute(class_current_sql)
    class_current = cursor.fetchall()
    cursor.execute(class_history_sql)
    class_history = cursor.fetchall()
    # student score data
    get_scores_sql = "SELECT name, date, score, subject, content FROM test WHERE (studentUID = '1800030') AND (name LIKE '%hsk%4%');"
    cursor.execute(get_scores_sql)
    scores = cursor.fetchall()
    return render_template("students.html", studentid=data[0], studentname=data[1], birth=data[2], phone=data[3], address=data[4], school=data[5], grade=data[6], class_current=class_current, class_history=class_history)

if __name__ == '__main__':
    app.run(debug=True)
