import os
from app import app, db
from flask import Flask, jsonify,session, render_template, request, redirect, url_for,flash,make_response, Response,send_from_directory
from functools import wraps
from app.facialauth import checkSamePerson
from datetime import datetime

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:            
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'alert-danger')
            return redirect(url_for('login'))
    return wrap

# Default route is home page
@app.route('/')

@app.route('/home')
@is_logged_in
def home_page():  
   # Create cursor
   cur = db.connection.cursor() 
   
   # Get articles
   result = cur.execute("select * from system_users")

   res = cur.fetchall()   
   return render_template('home.html', title = "home page", res=res)

@app.route('/login', methods=['GET', 'POST'])
def login():    
   if request.method == 'POST':
      # Get Form Fileds
      username = request.form['username']
      password_candidate = request.form['password']      
      
      # Create cursor
      cur = db.connection.cursor() 

      # Get articles
      sql = "select * from system_users where name = '{}';".format(username)
      result = cur.execute(sql)

      result = cur.fetchall()             
            
      if len(result) > 0 :             
         password = result[0]['pwd']
         
         user_id = result[0]['id']
         
         # Compare Passwords     
         # We put the hashed first then the sent value    
         # if bcrypt.check_password_hash(password, password_candidate):            
            # Passed
         if password_candidate == password :   
            session['logged_in'] = True
            session['username'] = username
            session['user_id'] = user_id                                 
            return redirect(url_for('home_page'))               
         else :            
            flash("Invalid Login", 'alert-danger')                  
            return render_template('login.html', title = "Login")            
      else :   
         flash("User Name Not Found", 'alert-danger')                  
         return render_template('login.html', title = "Login")
      
   return render_template('login.html', title = "Login")

@app.route('/logout')
def logout():
   session.clear()
   flash("Your are now logged out", 'alert-success')
   return redirect(url_for('login'))   

# System Users PK
@app.route('/takeattendance/<string:classID>')
@is_logged_in
# @is_allowed_view('show_system_rights')
def take_attendance(classID):   

   # # Get sysem modules
   # if len(fetch_system_rights(id)) > 0: 
   #    modulesList = fetch_system_rights(id)         
   # else :         
   #    modulesList = fetch_system_modules()         

   # if len(usersList) > 0:
   return render_template('take_attendance.html', title = "Take Attendance")
      # return render_template('take_attendance.html', title = "Take Attendance", takeAttendanceCursor=takeAttendanceCursor)
   # else:
   #    msg = 'No Users Found'
   #    return render_template('take_attendance.html', title = "System Rights", msg=msg)


@app.route('/faceauth', methods=['GET', 'POST'])
@is_logged_in
def face_auth():   
   image = request.args.get('base64Image');
   # print(image)
   # print(image)
   # res = checkSamePerson('images/omar.jpg', image, 'Y')
   res = checkSamePerson('images/omar.jpg', 'images/profile.jpg', 'N')
   return jsonify(data=res) 
   # return render_template('take_attendance.html', title = "Take Attendance")   