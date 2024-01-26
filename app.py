from flask import Flask, render_template, request, session, redirect, url_for
from random import randint
from smtplib import SMTP
from flask_mysqldb import MySQL
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'wertyui'

#----------File Upload Config-------
app.config['UPLOAD_FOLDER'] = 'static/blog_photos/'


#----------MySQL Config------------
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_PASSWORD'] = 'poiuytre'
app.config['MYSQL_DB'] = 'dbforblogs'

mysql = MySQL(app)


@app.route('/')
def index():
    if session.get('email'):
        # retrive all blogs from db
        cur = mysql.connection.cursor()
        sql_query = "SELECT blogs.blog_title, blogs.blog_des, blogs.blog_image, profile.full_name, blogs.datetime FROM blogs INNER JOIN profile ON blogs.blog_owner=profile.id;"
        cur.execute(sql_query)
        data_from_db = cur.fetchall()
        print(data_from_db)
        cur.close()

        # fetch session user info
        cur = mysql.connection.cursor()
        sql_query = f"SELECT full_name from profile where email = '{session['email']}';"
        cur.execute(sql_query)
        session_user_full_name = cur.fetchone()
        cur.close()

        return render_template('index.html', all_blogs = data_from_db, session_user_name = session_user_full_name)
    else:
        return render_template('login.html')


@app.route('/contact')
def contact():
    if session.get('email'):
        return render_template('contact.html')
    else:
        return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        if request.form.get('repassword') == request.form.get('password'):

            # fetch data from HTML form
            # set() - empty set
            global user_data
            user_data = {} #empty dictionary
            # user_data[new_key] = new_value # adding key value
            user_data['full_name'] = request.form.get('full_name')
            user_data['email'] = request.form.get('email')
            user_data['password'] = request.form.get('password')
            

            # generate OTP
            global c_otp
            c_otp = randint(100_000,999_999)
            message = f"Hello {user_data['full_name']}, your OTP is {c_otp}"


            # send OTP mail
            mail_obj = SMTP('smtp.gmail.com', 587)
            mail_obj.starttls()
            mail_obj.login('sameedirfan7@gmail.com','gjeqtlfmsenlbxpb')
            mail_obj.sendmail('sameedirfan7@gmail.com', user_data['email'], message)

            # render OTP page
            return render_template('otp.html')
        else:
            return render_template('otp.html', message="Both OTPs didn't match")


@app.route('/otp', methods=['POST', 'GET'])
def otp():
    if request.method == 'POST':
        if str(c_otp) == request.form.get('u_otp'):
            # create a row in our database
            cur = mysql.connection.cursor()
            sql_query = f"insert into profile values ({c_otp},'{user_data['full_name']}', '{user_data['email']}', '{user_data['password']}');"
            cur.execute(sql_query) # SQL query
            cur.connection.commit()
            cur.close()
            return render_template('register.html', message='successfully created!!!')
        else:

            return render_template('otp.html', message='Invalid OTP')
        
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        u_email = request.form.get('email')
        u_password = request.form.get('password')

        query = f"select full_name, email, password from profile where email = '{u_email}'"
        cur = mysql.connection.cursor()
        cur.execute(query)
        one_record = cur.fetchone()
        if one_record:
            # yes that email EXISTS
            if one_record[2] == u_password:
                #start a session
                session['email'] = u_email

                return redirect(url_for('index'))

                
            else:
                return render_template('login.html', message='incorrect password!!')
        else:
            # it does not exist
            return render_template('login.html', message='Invalid Email ID')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    del session['email']
    return render_template('login.html')


@app.route('/add_blog', methods=['GET', 'POST'])
def add_blog():
    if request.method == 'GET':
        return render_template('add_blog.html')
    else:
        #upload a blog
        # CREATE TABLE blogs (blog_id int NOT NULL AUTO_INCREMENT, blog_title varchar(255), blog_des text(65535), blog_image varchar(255), blog_owner int, PRIMARY KEY(blog_id), FOREIGN KEY(blog_owner) REFERENCES students(id) );
        b_title = request.form.get('title')
        b_des = request.form.get('des')
        b_file_obj = request.files['blog_pic']
        b_filename = b_file_obj.filename
        #below line will save image file in the folder
        b_file_obj.save(os.path.join(app.config['UPLOAD_FOLDER'], b_filename))

        cur = mysql.connection.cursor()
        #fetch current time
        current_dt = str(datetime.now())

        #fetch current user ID(session user)
        session_user_email = session['email']
        cur.execute(f"select id from profile where email = '{session_user_email}'")
        session_user_li = cur.fetchone()
        session_user_id = session_user_li[0]

        #saving info in the db/ creating a record in blogs
        sql_query = f"insert into blogs (blog_title, blog_des, blog_image, blog_owner, datetime ) values ('{b_title}','{b_des}', '{b_filename}', {session_user_id}, '{current_dt}');"
        cur.execute(sql_query) # SQL query
        cur.connection.commit()
        cur.close()



        return render_template('add_blog.html', message='Blog has been successfully added!!')


        
@app.route('/my_blogs')
def my_blogs():
    # exctract only session user's blogs
    session_user_email = session['email']
    cur = mysql.connection.cursor()
    sql_query = f"SELECT blogs.blog_title, blogs.blog_des, blogs.blog_image, profile.full_name, blogs.datetime FROM blogs INNER JOIN profile ON blogs.blog_owner=profile.id WHERE profile.email = '{session_user_email}';"
    cur.execute(sql_query)
    my_blogs = cur.fetchall()
    cur.close()
    return render_template('my_blogs.html', all_my_blogs = my_blogs)

#search bar query
# select * from blogs where blog_title in request.form.get('search_bar_name')

@app.route('/profile')
def profile():
    if 'email' not in session:
        return redirect(url_for('login'))
    else:
        cur = mysql.connection.cursor()
        # fetching data of logged-in user
        cur.execute("SELECT * FROM Profile WHERE email = % s", [session["email"]])
        profile = cur.fetchone()
        # closing connection
        cur.close()
        return render_template('profile.html', profile=profile, page="Profile")
    
    
    
@app.route("/edit_profile", methods=["GET","POST"])
def edit_profile():
        """
        This function is used to display Edit Profile Page and
        handle the POST method for updating User information into database.
        """
        if request.method == "POST":
            fullname = request.form['full_name']
            passw = request.form['password']
            # check if password was entered then update it otherwise leave it blank
            password = ""
            if len(request.form['password']) > 0 :
                password = request.form['password']
                # hashed password using bcrypt
                password = generate_password_hash(password, salt=rounds)
                # fire sql command to update user details
                userUpdateQuery =  "UPDATE Profile SET id=%d, full_name=%s, password=%s, Where email='%s'"\
                    .format(id, full_name, session['email'],password)
            else:
                userUpdateQuery = "UPDATE Profile SET id=%d, full_name=%s, password=%s, Where email='%s'"\
                    .format(id, full_name, session['email'],password)
            
            cur = mysql.connection.cursor()
            cur.execute(userUpdateQuery)
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('profile')) 


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('forgot_password.html')
    elif request.method == 'POST':
        user_email = request.form.get('email')

        cur = mysql.connection.cursor()
        sql_query = f"SELECT email, password FROM profile WHERE email = '{user_email}';"
        cur.execute(sql_query)
        user_data = cur.fetchone()
        cur.close()

        if user_data:
            # Prepare and send email
            recipient_email = user_data[0]
            password = user_data[1]
            sender_email = 'sameedirfan7@gmail.com'  
            message = f"Subject: Account Recovery\n\nYour email: {recipient_email}\n\nThis is your account email.\n Your Passowrd: {password}"
            
            mail_obj = SMTP('smtp.gmail.com', 587)
            mail_obj.starttls()
            mail_obj.login('sameedirfan7@gmail.com', 'gjeqtlfmsenlbxpb') 
            mail_obj.sendmail(sender_email, recipient_email, message) 
            
            mail_obj.quit()

            return render_template('render.html', message='Email sent successfully!')
        else:
            return render_template('forgot_password.html', message='Invalid Email ID')


#below codes send two different mail one for account recovery and password recovery

# @app.route('/forgot_password', methods=['GET', 'POST'])
# def forgot_password():
#     if request.method == 'GET':
#         return render_template('forgot_password.html')
#     elif request.method == 'POST':
#         user_email = request.form.get('email')

#         cur = mysql.connection.cursor()
#         sql_query = f"SELECT email, password FROM profile WHERE email = '{user_email}';"
#         cur.execute(sql_query)
#         user_data = cur.fetchone()
#         cur.close()

#         if user_data:
#             # Prepare and send email for account recovery
#             recipient_email = user_data[0]
#             sender_email = 'sameedirfan7@gmail.com'  # Update with your email
#             recovery_message = f"Subject: Account Recovery\n\nYour email: {recipient_email}\n\nThis is your account email."

#             mail_obj = SMTP('smtp.gmail.com', 587)
#             mail_obj.starttls()
#             mail_obj.login('sameedirfan7@gmail.com', 'gjeqtlfmsenlbxpb')  # Update with your credentials
#             mail_obj.sendmail(sender_email, recipient_email, recovery_message)

#             # Sending password via email
#             password = user_data[1]
#             password_message = f"Subject: Password Recovery\n\nYour password: {password}\n\nThis is your account password."

#             mail_obj.sendmail(sender_email, recipient_email, password_message)
#             mail_obj.quit()

#             return render_template('forgot_password.html', message='Email sent successfully!')
#         else:
#             return render_template('forgot_password.html', message='Invalid Email ID')


if __name__ == '__main__':
    app.run(debug=True)