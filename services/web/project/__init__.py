import os

from flask import (
    Flask,
    jsonify,
    send_from_directory,
    request,
    render_template,
    make_response
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import sqlalchemy
from sqlalchemy import text, create_engine
import psycopg2
import datetime


app = Flask(__name__)
app.config.from_object("project.config.Config")
db = SQLAlchemy(app)

engine = sqlalchemy.create_engine("postgresql://postgres:pass@postgres:5432", connect_args={
    'application_name': '__init__.py',
    })
connection = engine.connect()



@app.route('/')
def root():

    username = request.cookies.get('username')
    password = request.cookies.get('password')
    good_creds = check_creds(username,password)

    page_num = int(request.args.get('page', 1))
    offset = (page_num - 1) * 20


    result = connection.execute(text(
        "SELECT u.username, t.text, t.time "
        "FROM tweets AS t "
        "JOIN users AS u using(id_users) "
        "ORDER BY t.time DESC "
        "LIMIT :num OFFSET :off;"
        ), {"num": 20, "off": offset})

    rows = result.fetchall()

    messages = []
    for row in rows:
        messages.append({
            'username': row[0],
            'text': row[1],
            'time': row[2],
        })

    
    return render_template('root.html', logged_in=good_creds, messages=messages, page_num=page_num)

@app.route('/login', methods=['GET', 'POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    approved = check_creds(username,password)
    if username is None:
        return render_template('login.html', bad_creds=False, logged_in=False)
    else:
        if approved:

            # create cookie
            template = render_template('login.html', bad_creds=False, logged_in=True)
            response = make_response(template)
            response.set_cookie('username', username)
            response.set_cookie('password', password)
            return response
        else:
            return render_template('login.html', bad_creds=True, logged_in=False) 

@app.route('/logout')
def logout():
    
    #delete cookies
    response = make_response(render_template('logout.html'))
    response.delete_cookie('username')
    response.delete_cookie('password')

    return response 

@app.route('/create_account', methods=['GET', 'POST'])
def create_account():

    username = request.form.get('username')
    password = request.form.get('password')
    password2 = request.form.get('password2')
    if username is not None and password is not None and password2 is not None and username and password and password2:
        if (password != password2):
            return render_template('create_account.html', mismatch=True, taken=False, empty=False, done=False)
        elif check_taken(username):
            return render_template('create_account.html', mismatch=False, taken=True, empty=False, done=False)
        else:
            sql = sqlalchemy.sql.text('''
                INSERT INTO users (username, password)
                VALUES (:username, :password)
            ''')

            res = connection.execute(sql, {
                'username': username,
                'password': password
            })
            return render_template('create_account.html', mismatch=False, taken=False, empty=False, done=True)
    else:
        return render_template('create_account.html', mismatch=False, taken=False, empty=True, done=False)

@app.route('/create_message', methods=['GET', 'POST'])
def create_message():

    message = request.form.get('message')
    
    username = request.cookies.get('username')
    password = request.cookies.get('password')
    good_creds = check_creds(username,password)

    if good_creds and message is not None:
        insert_tweet(message, username)
        return render_template('create_message.html',logged_in=good_creds, message_inserted=True)

    return render_template('create_message.html',logged_in=good_creds, message_inserted=False)

@app.route('/search', methods=['GET','POST'])
def search():

    username = request.cookies.get('username')
    password = request.cookies.get('password')
    good_creds = check_creds(username,password)

    search = request.form.get('search')
    if search:

        page_num = int(request.args.get('page', 1))
        offset = (page_num - 1) * 20

        sql = sqlalchemy.sql.text("""
            SELECT id_tweets,
            ts_headline('english', text, plainto_tsquery(:query), 'StartSel=<span> StopSel=</span>') AS highlighted_text,
            time,
            id_users
            FROM tweets
            WHERE to_tsvector('english', text) @@ plainto_tsquery(:query)
            ORDER BY time DESC
            LIMIT 20 OFFSET :offset;
        """)

        result = connection.execute(sql, {'query': ' & '.join(search.split()), 'offset': offset})
        
        

        rows = result.fetchall()

        # find corresponding usernames then append all information to messages
        messages = []
        for row in rows:
            sql = sqlalchemy.sql.text("""
                SELECT username
                FROM tweets
                JOIN users USING(id_users)
                WHERE id_tweets=:id ;
            """)
            result = connection.execute(sql, {'id': row[0]})

            users = result.fetchone()

            messages.append({
                'username': users[0][0],
                'text': row[1],
                'time': row[2],
            })



        return render_template('search.html',logged_in=good_creds, messages=messages, page_num=page_num, display=True)

    return render_template('search.html',logged_in=good_creds, page_num=1, display=False)



#helper functions:
def check_creds(username, password):
   
    if not username or not password:
        return False

    if username is None or password is None:
        return False

    sql = sqlalchemy.sql.text('''
        SELECT * FROM users
        WHERE username = :username
        AND password = :password;
        ''')

    res = connection.execute(sql, {
        'username': username,
        'password': password
    })

    # if there is a user with the corresponding username and password, then the query will have a non empty result
    if res.fetchone() is None:
        return False
    else:
        return True

def check_taken(username):
    sql = sqlalchemy.sql.text('''
        SELECT username FROM users
        WHERE username = :username;
        ''')

    res = connection.execute(sql, {
        'username': username
    })
    
    # if there is a user with the corresponding username then it query qill have a non empty result (username taken)
    if res.fetchone() is None:
        return False
    else:
        return True

def insert_tweet(text, username):
    
    sql = sqlalchemy.sql.text('''
        SELECT id_users FROM users
        WHERE username = :username;
        ''')

    result_id_users = connection.execute(sql, {'username': username})
    id_users = result_id_users.fetchone()[0]  # Fetch the result and extract the value

    sql = sqlalchemy.sql.text('''
        SELECT MIN(u.id_urls)               
        FROM urls u
        LEFT JOIN tweets t ON u.id_urls = t.id_urls
        WHERE t.id_urls IS NULL;
        ''')

    result_id_urls = connection.execute(sql)
    id_urls = result_id_urls.fetchone()[0]  # Fetch the result and extract the value

    time = str(datetime.datetime.now()).split('.')[0] + '.' + str(datetime.datetime.now()).split('.')[1]


    sql = sqlalchemy.sql.text(
            '''
            INSERT INTO tweets (text, id_users, id_urls, time) 
            VALUES (:text, :id_users, :id_urls, :time)
            ''')

    sql = sql.bindparams(text=text,
        id_users=id_users,
        id_urls=id_urls,
        time=time)
    connection.execute(sql)

