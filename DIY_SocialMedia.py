# GOAL: Create a website that has
#       - user auth(with username) WITH password hashing
#       - parsing and organising data from API calls into data structures and classes
#       - a page where people POST comments (prolly a class that gets user info from session)
#       - Potential strategy:
#           -> A user authorises themselves, sees a landing page with API data and a comment form
#           -> When they write stuff in it and hit submit, it gets received by a route that MAYBE validates
#              the input, then it gets sent to the postgresql database with the user's username
#              as a neighbor column
#           -> That landing page has a hyperlink to the comments page
#           -> That comment page's route gets EVERY username and comment from the db, makes a comment object
#           -> And puts it in a persistent list(learn this), that list gets sent to the comment page's html
#           -> Using jinja2, the list of objects gets iterated over with a for loop everytime a user visits
#              the site, and the object's data gets treated as a comment box widget showing the username and
#              form data(i.e the comment)
#           -> use one table for the id, email, password, use another table with a FOREIGN KEY
#              for the user_comment, the second table can have duplicate but NOT the first, you fetch the
#              username from table 1 and user_comment from table 2 using the FOREIGN KEY

#       |_^_| Effectively creating a DIY social media site (if the project works then put it in render)

from flask import Flask, redirect, url_for, request, render_template, session
from flask_login import LoginManager, login_required, login_user, logout_user, current_user, UserMixin
import psycopg2
import os
from Auth_Training2 import signup, login
import operator
from werkzeug.security import check_password_hash
from dotenv import load_dotenv

app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "bouncer"

load_dotenv("shush.env")

app.config["SECRET_KEY"] = os.getenv("secret_key") # FILL THIS IN WHEN YOU MAKE THE RENDER SITE

class User(UserMixin):
    def __init__(self, user_id):
        self.user_id = user_id
    def get_id(self):
        return self.user_id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "POST":
        db_url = os.environ.get("DATABASE_URL")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("create table if not exists user_comment_bank (comment_id serial primary key,"
                       "referral_id integer references user_comment_auth(given_id) on delete cascade,"
                       "comment_content text)")

        comment = request.form.get("comment")
        if comment.strip() == "":
            conn.commit()
            conn.close()
            return render_template("comment_writing.html", verdict="dude, you can't just"
                                                                 "hit submit but not write anything")
        if any(letter.isalpha() for letter in comment):
            cursor.execute("insert into user_comment_bank (comment_content, referral_id) values (%s, %s)",
                           (comment, session.get("anchor")))
            conn.commit()
            conn.close()
            return render_template("comment_writing.html", verdict="Your message went through,"
                                                                   " welcome to the crew playa")

    return render_template("comment_writing.html")

@app.route("/bouncer", methods=["GET", "POST"])
def bouncer():
    if request.method == "POST":
        username = request.form.get("username")
        signup_email = request.form.get("signup_email")
        signup_password = request.form.get("signup_password")

        login_email = request.form.get("login_email")
        login_password = request.form.get("login_password")

        signup_check = signup(signup_email, signup_password, username)
        login_check = login(login_email, login_password)
        if operator.xor(bool(signup_check), bool(login_check)):
            if signup_check:
                param = (signup_email,)
                final_password = signup_password
            else:
                param = (login_email,)
                final_password = login_password

            db_url = os.environ.get("DATABASE_URL")

            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            cursor.execute("select * from user_comment_auth where email = %s",
                           param)
            raw_row = cursor.fetchone()
            given_id = raw_row[0]
            session["anchor"] = given_id  # allows the landing page to do table stuff with the given_id's row
            if check_password_hash(raw_row[2], final_password):
                netizen = User(given_id)
                login_user(netizen)
                conn.commit()
                conn.close()
                return redirect(url_for("home"))
            else:
                return render_template("user_auth2.html", error="shit, FUCK, something went'"
                                                                "horribly wrong")
        else:
            return render_template("user_auth2.html", error="shit, FUCK, something went'"
                                                            "horribly wrong")

    return render_template("user_auth2.html")

@app.route("/comment_board")
@login_required
def comment_board():
    # NEXT STEP: open the database, fetch ALL rows, but only get two columns (username, comment) and put it
    # in this list
    db_url = os.environ.get("DATABASE_URL")

    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    cursor.execute("select t2.comment_content, t1.username from user_comment_auth t1 join user_comment_bank t2"
                   " on t2.referral_id = t1.given_id")
    comment_username = cursor.fetchall()
    print(comment_username)
    return render_template("comment_display.html", comment_username = comment_username)

if __name__ == "__main__":
    app.run(debug=True)
