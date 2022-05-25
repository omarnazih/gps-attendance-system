import os
import base64
from app import app, db
from werkzeug.utils import secure_filename
from flask import Flask, jsonify,session, render_template, request, redirect, url_for,flash,make_response, Response,send_from_directory
from functools import wraps
from app.facialauth import checkSamePerson
import datetime

def ifEmpty(var, val):
  if var == '':
    return val
  return var

def nvl(var):
  if var == '':
    return 'null'
  return var

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
         is_admin = result[0]['admin']
         is_student = result[0]['student']
         is_teacher = result[0]['teacher']         
         
         # Compare Passwords     
         # if bcrypt.check_password_hash(password, password_candidate):            
            # Passed
         if password_candidate == password :   
            session['logged_in'] = True
            session['username'] = username
            session['user_id'] = user_id 
            session['is_admin'] = is_admin                                
            session['is_student'] = is_student                                
            session['is_teacher'] = is_teacher 

            if session['is_student'] == 'Y':
               cur.execute(f"select id from students where user_id = {session['user_id']}")
               res = cur.fetchone()
               session['student_id'] = res['id']

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

@app.route('/students')
@is_logged_in
def students():    
   # Create cursor
   cur = db.connection.cursor() 

   # Get System Users
   cur.execute("SET @row_number = 0;")               
   result = cur.execute("select (@row_number:=@row_number + 1) AS row_num, students.* from students")
   studentData = cur.fetchall()   

   result = cur.execute("select id, name from years")
   yearsCombo = cur.fetchall()      

   result = cur.execute("select id, name from majors")
   majorsCombo = cur.fetchall()      

   result = cur.execute("select id, name from system_users")
   usersCombo = cur.fetchall()

   return render_template('students.html', title = "students", studentData = studentData, yearsCombo= yearsCombo, majorsCombo=majorsCombo, usersCombo=usersCombo )

@app.route('/save_student', methods=['GET', 'POST'])
@is_logged_in
def save_student():    
   # Create cursor
   cur = db.connection.cursor()      

   #Storing Data into variables
   id = request.form.getlist('id')
   code = request.form.getlist('code')    
   name = request.form.getlist('name')  
   major = request.form.getlist('major') 
   year = request.form.getlist('year') 
   picture = request.files.getlist('picture')  
   user = request.form.getlist('user') 

   #Getting lenght of a required value list
   listLength = len(id)
   
   if listLength > 1:         
      for x in range (0, listLength):    
         print(code[x])     
         print(major[x])     
         print(year[x])     
         print(user[x])     
               
         file_name = secure_filename(picture[x].filename);                      
         # If The path is correct then save      
         if file_name != '': 
            absolute_path = os.path.abspath(app.config['IMAGES_FOLDER'] + file_name)               
            picture[x].save(absolute_path)
            absolute_path = absolute_path.replace('\\','\\\\')
         else:
            absolute_path = 'null'         

         if id[x] == '':
            cur.execute("select IFNULL(max(id),0)+1 as id from students")
            res = cur.fetchone()        
            id = res['id']                        

            sql = f"""
                  insert into students (id, code, name, major_id, year_id, picture, user_id)
                  values ({id}, '{code[x]}' , '{ifEmpty(name[x], 'null')}', {ifEmpty(major[x], 'null')}, {ifEmpty(year[x], 'null')}, "{absolute_path}", {ifEmpty(user[x], 'null')});      
                  """               
         else:
            sql = f"""
                  update 
                     students
                  set 
                      code = '{code[x]}',
                      name = '{name[x]}',
                      major_id = '{nvl(major[x])}',
                      year_id = {nvl(year[x])},
                      picture = "{absolute_path}",
                      user_id = {nvl(user[x])}
                  where 
                     id = {id[x]};      
                  """     
         print(sql)                       
         result = cur.execute(sql)      
         db.connection.commit()    
      # FeedBack
      flash('Data Updated Successfully', 'alert-success')                                                                               
   elif listLength == 1 :   
      file_name = secure_filename(picture[0].filename);             
      
      # If The path is correct then save      
      if file_name != '': 
         absolute_path = os.path.abspath(app.config['IMAGES_FOLDER'] + file_name)               
         picture[0].save(absolute_path)
         absolute_path = absolute_path.replace('\\','\\\\')
      else:
         absolute_path = 'null'                                
      #If Id is null insert new user
      if id[0] == '':
         cur.execute("select IFNULL(max(id),0)+1 as id from classes")
         res = cur.fetchone()        
         id = res['id']                     
         sql = f"""
               insert into students (id, code, name, major_id, year_id, picture, user_id)
               values ({id}, '{code[0]}' , '{name[0]}', {ifEmpty(major[0], 'null')}, {ifEmpty(year[0], 'null')}, "{absolute_path}", {nvl(user[0])});        
               """             
      else :   
            sql = f"""
                  update 
                     students
                  set 
                      code = '{code[0]}',
                      name = '{name[0]}',
                      major_id = '{major[0]}',
                      year_id = {year[0]},
                      picture = "{absolute_path}",
                      user_id = {user[0]}
                  where 
                     id = {id[0]}; 
                  """    
      print(sql)                                             
      result = cur.execute(sql)      
      db.connection.commit()          
      flash('Data Updated Successfully', 'alert-success')                     
   else :    
      flash('Please Add At least one record before saving ', 'alert-info') 

   return redirect(url_for('students'))

@app.route('/classes')
@is_logged_in
def classes():    
   # Create cursor
   cur = db.connection.cursor() 

   # Get System Users
   cur.execute("SET @row_number = 0;")               
   result = cur.execute("select (@row_number:=@row_number + 1) AS row_num, classes.* from classes")
   classData = cur.fetchall()   

   result = cur.execute("select id, name from years")
   yearsCombo = cur.fetchall()      

   result = cur.execute("select id, name from majors")
   majorsCombo = cur.fetchall()      


   return render_template('classes.html', title = "Classes", classData = classData, yearsCombo= yearsCombo, majorsCombo=majorsCombo )


@app.route('/del_class/<int:classID>')
@is_logged_in
def delete_class(classID):    
   # Create cursor
   cur = db.connection.cursor() 

   sql = f"delete from attendance where class_id = {classID}"
   cur.execute(sql)
   db.connection.commit()        

   sql = f"delete from students where class_id = {classID}"
   cur.execute(sql)
   db.connection.commit()        

   sql = f"delete from classes where id = {classID}"
   cur.execute(sql)
   db.connection.commit()        

   sql = f"select * from classes"
   classData = cur.execute(sql)
      
   return redirect(url_for('classes'))     

@app.route('/save_class', methods=['GET', 'POST'])
@is_logged_in
def save_class():    
   # Create cursor
   cur = db.connection.cursor()      

   #Storing Data into variables
   id = request.form.getlist('id')
   code = request.form.getlist('code')    
   name = request.form.getlist('name')  
   desc = request.form.getlist('desc')  
   lat = request.form.getlist('lat')  
   lang = request.form.getlist('lang')  
   major = request.form.getlist('major') 
   year = request.form.getlist('year') 

   #Getting lenght of a required value list
   listLength = len(id)

   if listLength > 1:    
      for x in range (0, listLength):                                            
         if id[x] == '':
            cur.execute("select IFNULL(max(id),0)+1 as id from classes")
            res = cur.fetchone()        
            id = res['id']                        
            
            sql = f"""
                  insert into classes (id, code, name, description, loc_lat, loc_lang, major_id, year_id)
                  values ({id}, '{code[x]}' , '{name[x]}', '{desc[x]}', {lat[x]}, {lang[x]}, {ifEmpty(major[x], 'null')}, {ifEmpty(year[x], 'null')});      
                  """               
         else:
            sql = f"""
                  update 
                     classes
                  set 
                      code = '{code[x]}',
                      name = '{name[x]}',
                      description = '{desc[x]}',
                      loc_lat = {lat[x]},
                      loc_lang = {lang[x]},
                      major_id = {major[x]},
                      year_id = {year[x]}
                  where 
                     id = {id[x]};      
                  """                   
         result = cur.execute(sql)      
         db.connection.commit()    
      # FeedBack
      flash('Data Updated Successfully', 'alert-success')                                                                               
   elif listLength == 1 :                                                  
      #If Id is null insert new user
      if id[0] == '':
         cur.execute("select IFNULL(max(id),0)+1 as id from classes")
         res = cur.fetchone()        
         id = res['id']                     
         sql = f"""
               insert into classes (id, code, name, description, loc_lat, loc_lang, major_id, year_id)
               values ({id}, '{code[0]}' , '{name[0]}', '{desc[0]}', {lat[0]}, {lang[0]}, {ifEmpty(major[0], 'null')}, {nvl(year[0])});      
               """             
      else :   
            sql = f"""
                  update 
                     classes
                  set 
                      code = '{code[0]}', 
                      name = '{name[0]}',
                      description ='{desc[0]}',
                      loc_lat = {lat[0]},
                      loc_lang = {lang[0]},
                      major_id = {major[0]},
                      year_id = {year[0]}                      
                  where 
                     id = {id[0]};
                  """        
      result = cur.execute(sql)      
      db.connection.commit()          
      flash('Data Updated Successfully', 'alert-success')                     
   else :    
      flash('Please Add At least one record before saving ', 'alert-info') 

   return redirect(url_for('classes'))     

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

   elif request.method == 'POST' and session['is_student'] == 'Y' :
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
   else :
      return jsonify(response="Something went wrong!!")                        

@app.route('/faceauth', methods=['GET', 'POST'])
@is_logged_in
def face_auth():   
   # Create cursor
   cur = db.connection.cursor() 

   json = request.get_json();   
   image = json['picture']
   classID = json['classIDVal']

   cur.execute(f"select picture from students where id = {session['student_id']}")
   picPath = cur.fetchone()

   res = checkSamePerson(picPath['picture'], image, 'Y')
      
   sql = "select * from classes where id = '{}';".format(classID)
   result = cur.execute(sql)
   classData = cur.fetchone()  

   if res == True:
      return jsonify(isSamePerson="True", classData = classData) 
   else :
      return jsonify(isSamePerson="False", classData = classData) 


   