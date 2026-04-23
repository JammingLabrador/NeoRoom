import psycopg2
import os
from werkzeug.security import generate_password_hash, check_password_hash

def signup(form_email, form_password, form_username):
    db_url = os.environ.get("DATABASE_URL")

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    cursor.execute("""create table if not exists user_comment_auth (given_id serial primary key, 
                    email text, password text, username text)""")

    a_okay = False
    email_good = False
    password_good = False
    password_has_nums = any(letter.isdigit() for letter in form_password)
    username_good = False

    if form_email.endswith(("@gmail.com", "@outlook.com", "@yahoo.com")):
        email_good = True
    if len(form_password) > 5 and password_has_nums:
        hashed_password = generate_password_hash(form_password)
        password_good = True
    if form_username and len(form_username.strip()) > 3:
        username_good = True

    cursor.execute("select * from user_comment_auth")
    result = cursor.fetchall()
    for row in result:
        if form_email == row[1]:
            conn.close()
            return a_okay

    if email_good and password_good and username_good:
        cursor.execute("insert into user_comment_auth (email, password, username) values (%s, %s, %s)",
                       (form_email, hashed_password, form_username))
        conn.commit()
        conn.close()
        a_okay = True
        return a_okay

    conn.close()
    return a_okay


def login(form_email, form_password):
    a_okay = False
    db_url = os.environ.get("DATABASE_URL")

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    cursor.execute("select * from user_comment_auth where email = %s",
                   (form_email,))
    result = cursor.fetchone()
    conn.close()

    if result and check_password_hash(result[2], form_password):
        a_okay = True
        return a_okay

    return a_okay
