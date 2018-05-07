# -*- coding: UTF-8 -*-
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, json
#from data import Feedbacks
#from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from wtforms.fields.html5 import DateField
from wtforms_components import TimeField, DateRange
from passlib.hash import sha256_crypt
from functools import wraps
from datetime import date, datetime

#### sqlite
import sqlite3#
from flask import g#
DATABASE = 'database.db'#
#### sqlite

app = Flask(__name__)
app.url_map.strict_slashes = False

# # Config MySQL
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = '123456'
# app.config['MYSQL_DB'] = 'bciyuf'
# app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# # init MYSQL
# mysql = MySQL(app)


#Feedbacks = Feedbacks()

####
def connection():#
    db = getattr(g, '_database', None)#
    if db is None:#
        db = g._database = sqlite3.connect(DATABASE)#
        db.row_factory = make_dicts
    return db#

@app.teardown_appcontext#
def close_connection(exception):#
    db = getattr(g, '_database', None)#
    if db is not None:#
        db.close()#

def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))
####

# Index
@app.route('/')
def index():
    return render_template('home.html')


# About
@app.route('/about')
def about():
    return render_template('about.html')


# Feedback Ok
@app.route('/feedbacks')
def feedbacks():
    # Create cursor
    # cur = mysql.connection.cursor()
    cur = connection().cursor()#

    # Get feedbacks
    # result = cur.execute("SELECT * FROM feedbacks")

    # feedbacks = cur.fetchall()

    cur.execute("SELECT count(*) FROM feedbacks")#
    # if result > 0:
    if cur.fetchone()['count(*)'] > 0:#
        cur.execute("SELECT * FROM feedbacks")#
        feedbacks = cur.fetchall()#
        return render_template('feedbacks.html', feedbacks=feedbacks)
    else:
        msg = '目前沒有回饋'
        return render_template('feedbacks.html', msg=msg)
    # Close connection
    cur.close()

#Single Feedback
@app.route('/feedback/<string:id>/')
def feedback(id):
    # Create cursor
    # cur = mysql.connection.cursor()
    cur = connection().cursor()#

    # Get feedback
    # result = cur.execute("SELECT * FROM feedbacks WHERE id = %s", [id])
    result = cur.execute("SELECT * FROM feedbacks WHERE id = ?", [id])#

    feedback = cur.fetchone()#

    return render_template('feedback.html', feedback=feedback)


# Register Form Class
class RegisterForm(Form):
    username = StringField('使用者名稱', [validators.Length(min=4, max=20, message='使用者名稱長度為 4 ~ 20')])
    nickname = StringField('暱稱', [validators.Length(min=1, max=10, message='暱稱長度為 1 ~ 10')])
    email = StringField('信箱', [validators.Length(min=6, max=50, message='信箱長度為 6 ~ 50')])
    password = PasswordField('密碼', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='輸入的密碼不同')
    ])
    confirm = PasswordField('確認密碼')


# User Register Ok
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        nickname = form.nickname.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        # cur = mysql.connection.cursor()
        cur = connection().cursor()#

        # Execute query
        # cur.execute("INSERT INTO users(username, nickname, email, password) VALUES(%s, %s, %s, %s)", (username, nickname, email, password))
        cur.execute("INSERT INTO users(username, nickname, email, password) VALUES(?, ?, ?, ?)", (username, nickname, email, password))#

        # Commit to DB
        # mysql.connection.commit()
        connection().commit()#

        # Close connection
        cur.close()

        flash('註冊成功! 現在可以登入囉~', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# User login Ok
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        # cur = mysql.connection.cursor()
        cur = connection().cursor()#

        # Get user by username
        # result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
        cur.execute("SELECT count(*) FROM users WHERE username = ?", [username])#
        # if result > 0:
        if cur.fetchone()['count(*)'] > 0:#
            # Get stored hash
            # password = data['password']
            cur.execute("SELECT * FROM users WHERE username = ?", [username])#
            password = cur.fetchone()['password']#

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('你已登入', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = '無效的登入'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = '找不到使用者名稱'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('想看?! 請先登入', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('你已登出', 'success')
    return redirect(url_for('login'))

# Dashboard #這裡要改很多~_~
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    # cur = mysql.connection.cursor()
    cur = connection().cursor()

    # Get feedbacks
    # result = cur.execute("SELECT * FROM feedbacks")

    # feedbacks = cur.fetchall()

    cur.execute("SELECT count(*) FROM feedbacks WHERE author = ?", [session['username']])#
    # if result > 0:
    if cur.fetchone()['count(*)'] > 0:#
        cur.execute("SELECT * FROM feedbacks WHERE author = ?", [session['username']])#
        feedbacks = cur.fetchall()#
        return render_template('dashboard.html', feedbacks=feedbacks)
    else:
        msg = '目前沒有約'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()

# Feedback Form Class
class FeedbackForm(Form):
    title = StringField('標題', [validators.Length(min=1, max=10, message="長度有誤 (1 ~ 10)")])
    day = DateField('日期', default=date.today, format='%Y-%m-%d', validators=[validators.DataRequired(message="日期有誤")])
    time = TimeField('時間', default=datetime.now(), format='%H:%M:%S')
    place = StringField('地點', [validators.Length(min=1, max=50, message="長度有誤 (1 ~ 50)")])
    content = TextAreaField('回饋', [validators.Length(min=1, max=500, message="長度有誤 (10 ~ 500)")])

# Add Feedback
@app.route('/add_feedback', methods=['GET', 'POST'])
@is_logged_in
def add_feedback():
    form = FeedbackForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        day = form.day.data
        time = form.time.data
        place = form.place.data
        content = form.content.data
        # Create Cursor
        # cur = mysql.connection.cursor()
        cur = connection().cursor()
        # Execute
        # cur.execute("INSERT INTO feedbacks(title, content, author) VALUES(%s, %s, %s)",(title, content, session['username']))
        cur.execute("INSERT INTO feedbacks(title, day, time, place, author, content, create_date) VALUES(?, ?, ?, ?, ?, ?, ?)",(title, str(day), str(time), place, session['username'], content, str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))

        # Commit to DB
        # mysql.connection.commit()
        connection().commit()#

        #Close connection
        cur.close()

        flash('回饋填寫成功', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_feedback.html', form=form)


# Edit Feedback
@app.route('/edit_feedback/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_feedback(id):
    # Create cursor
    # cur = mysql.connection.cursor()
    cur = connection().cursor()

    # Get feedback by id
    # result = cur.execute("SELECT * FROM feedbacks WHERE id = %s", [id])
    result = cur.execute("SELECT * FROM feedbacks WHERE id = ?", [id])

    feedback = cur.fetchone()
    cur.close()
    # Get form
    form = FeedbackForm(request.form)

    # Populate feedback form fields
    form.title.data = feedback['title']
    form.day.data = feedback['day']
    form.time.data = feedback['time']
    form.place.data = feedback['place']
    form.content.data = feedback['content']

    print(form.validate())
    if request.method == 'POST' and form.validate():
        title = request.form['title']
        content = request.form['content']

        # Create Cursor
        # cur = mysql.connection.cursor()
        cur = connection().cursor()#
        app.logger.info(title)
        # Execute
        # cur.execute ("UPDATE feedbacks SET title=%s, content=%s WHERE id=%s",(title, content, id))
        cur.execute ("UPDATE feedbacks SET title=?, content=? WHERE id=?",(title, content, id))
        # Commit to DB
        # mysql.connection.commit()
        connection().commit()#

        # Close connection
        cur.close()

        flash('回饋已更新', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_feedback.html', form=form)

# Delete Feedback
@app.route('/delete_feedback/<string:id>', methods=['POST'])
@is_logged_in
def delete_feedback(id):
    # Create cursor
    # cur = mysql.connection.cursor()
    cur = connection().cursor()

    # Execute
    cur.execute("DELETE FROM feedbacks WHERE id = ?", [id])

    # Commit to DB
    # mysql.connection.commit()
    connection().commit()#

    # Close connection
    cur.close()

    flash('回饋已刪除', 'success')

    return redirect(url_for('dashboard'))


# Feedback Form Class
class DateForm(Form):
    day = DateField('日期', default=datetime.today, format='%Y-%m-%d')
    time = TimeField('時間', default=datetime.now(), format='%H:%M:%S')
    place = StringField('地點', [validators.Length(min=1, max=10)])

# Date
@app.route('/date', methods=['GET', 'POST'])
@is_logged_in
def date():
    form = DateForm(request.form)
    if request.method == 'POST' and form.validate():
        day = form.day.data
        time = form.time.data
        place = form.place.data

        # Create Cursor
        cur = connection().cursor()

        # Execute
        cur.execute("INSERT INTO dates(dater, day, time, place) VALUES(?, ?, ?, ?)",(session['username'], str(day), str(time), place))

        # Commit to DB
        # mysql.connection.commit()
        connection().commit()#

        #Close connection
        cur.close()

        flash('約成功囉!', 'success')

        return redirect(url_for('dashboard'))

    return render_template('date.html', form=form)

# TimeTable
@app.route('/timetable')
def timetable():
    return render_template('timetable.html')

@app.errorhandler(404)
def page_not_found(e):
    flash('沒找到頁面 但你發現了柏辰', 'danger')
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.secret_key='oh@my@fl@g'
    #app.run(host='0.0.0.0', port=8787, threaded=True)
    app.run(debug=True)