from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from data import topics
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '123456'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

Topics = Topics()

# Index
@app.route('/')
def index():
    return render_template('home.html')


# About
@app.route('/about')
def about():
    return render_template('about.html')


# topics
@app.route('/topics')
def topics():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get topics
    result = cur.execute("SELECT * FROM topics")

    topics = cur.fetchall()

    if result > 0:
        return render_template('topics.html', topics=topics)
    else:
        msg = 'No Topics Found'
        return render_template('topics.html', msg=msg)
    # Close connection
    cur.close()


#Single topic
@app.route('/topic/<string:id>/')
def topic(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get topic
    result = cur.execute("SELECT * FROM topics WHERE id = %s", [id])

    topic = cur.fetchone()

    return render_template('topic.html', topic=topic)


# Register Form Class
# class RegisterForm(Form):
#     name = StringField('Name', [validators.Length(min=1, max=50)])
#     username = StringField('Username', [validators.Length(min=4, max=25)])
#     email = StringField('Email', [validators.Length(min=6, max=50)])
#     password = PasswordField('Password', [
#         validators.DataRequired(),
#         validators.EqualTo('confirm', message='Passwords do not match')
#     ])
#     confirm = PasswordField('Confirm Password')


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get topics
    result = cur.execute("SELECT * FROM topics")

    topics = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', topics=topics)
    else:
        msg = 'No Topics Found'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()

# Topic Form Class
# class topicForm(Form):
#     title = StringField('Title', [validators.Length(min=1, max=200)])
#     body = TextAreaField('Body', [validators.Length(min=30)])

# Add topic
@app.route('/add_topic', methods=['GET', 'POST'])
@is_logged_in
def add_topic():
    form = topicForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO topics(title, body, author) VALUES(%s, %s, %s)",(title, body, session['username']))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Topic Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_topic.html', form=form)


# Edit topic
@app.route('/edit_topic/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_topic(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get topic by id
    result = cur.execute("SELECT * FROM topics WHERE id = %s", [id])

    topic = cur.fetchone()
    cur.close()
    # Get form
    form = topicForm(request.form)

    # Populate topic form fields
    form.title.data = topic['title']
    form.body.data = topic['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)
        # Execute
        cur.execute ("UPDATE topics SET title=%s, body=%s WHERE id=%s",(title, body, id))
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Topic Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_topic.html', form=form)

# Delete topic
@app.route('/delete_topic/<string:id>', methods=['POST'])
@is_logged_in
def delete_topic(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM topics WHERE id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Topic Deleted', 'success')

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
