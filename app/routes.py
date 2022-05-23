import os
import base64
from app import app, db
from flask import Flask, jsonify,session, render_template, request, redirect, url_for,flash,make_response, Response,send_from_directory
from functools import wraps
from app.facialauth import checkSamePerson
import datetime

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
   
   # Get System Users
   result = cur.execute("select * from classes")
   classData = cur.fetchall()   

   return render_template('home.html', title = "home page", classData = classData)

@app.route('/login', methods=['GET', 'POST'])
def login():    
   if request.method == 'POST':
      # Get Form Fileds
      username = request.form['username']
      password_candidate = request.form['password']      
      
      # Create cursor
      cur = db.connection.cursor() 

      # Get system users
      sql = "select * from system_users where name = '{}';".format(username)
      result = cur.execute(sql)
      result = cur.fetchall()             
            
      if len(result) > 0 :             
         password = result[0]['pwd']         
         user_id = result[0]['id']
         
         # Compare Passwords     
         # if bcrypt.check_password_hash(password, password_candidate):            
            # Passed
         if password_candidate == password :   
            session['logged_in'] = True
            session['username'] = username
            session['user_id'] = user_id                                 
            return redirect(url_for('home_page'))               
         else :            
            flash("Invalid Login", 'alert-danger')                  
            return render_template('login.html')            
      else :   
         flash("User Name Not Found", 'alert-danger')                  
         return render_template('login.html')
      
   return render_template('login.html')

@app.route('/logout')
def logout():
   session.clear()
   return redirect(url_for('login'))   

@app.route('/classes')
@is_logged_in
def classes():    
   # Create cursor
   cur = db.connection.cursor() 
   
   # Get System Users
   result = cur.execute("select * from classes")
   classData = cur.fetchall()   

   return render_template('classes.html', title = "Classes", classData = classData)

@app.route('/takeattendance/<string:classID>', methods=['GET', 'POST'])
@is_logged_in
def take_attendance(classID):   
   # Create cursor
   cur = db.connection.cursor() 

   if request.method == 'GET':

      # Get Data
      sql = "select * from classes where id = '{}';".format(classID)
      result = cur.execute(sql)
      classData = cur.fetchone()  

      return render_template('take_attendance.html', title = "Take Attendance", classData = classData)

   elif request.method == 'POST':
      CurrentDate=datetime.date.today()  
      
      cur.execute("select id from students where user_id = {}".format(session['user_id']))
      res = cur.fetchone()        
      student_id = res['id']

      cur.execute("select IFNULL(max(id),0)+1 as id from attendance")
      res = cur.fetchone()        
      attendance_id = res['id']
      
      cur.execute(f"select 1 as val from attendance where date = '{CurrentDate}' and student_id = {student_id} and class_id= {classID}")
      res = cur.fetchone() 

      if res == None:          
         # Insert Data
         sql = """
               insert into attendance (id, date, student_id, class_id)
               values ({}, '{}' , {}, {});      
               """.format(attendance_id, CurrentDate, student_id, classID)
               
         result = cur.execute(sql)      
         db.connection.commit()      
         
         return jsonify(response="Success")    
         
      else :   
         return jsonify(response="Attendance Taken Before")                  

@app.route('/faceauth', methods=['GET', 'POST'])
@is_logged_in
def face_auth():   
   json = request.get_json();   
   image = json['picture']
   classID = json['classIDVal']

   res = checkSamePerson(app.config['IMAGES_FOLDER']+'/omar.jpg', image, 'Y')
   
   # Create cursor
   cur = db.connection.cursor() 

   # Get system users
   sql = "select * from classes where id = '{}';".format(classID)
   result = cur.execute(sql)
   classData = cur.fetchone()  

   if res == True:
      return jsonify(isSamePerson="True", classData = classData) 
   else :
      return jsonify(isSamePerson="False", classData = classData) 

# absolute_path = os.path.abspath(app.config['UPLOAD_FOLDER'] + secure_filename(f.filename))


   