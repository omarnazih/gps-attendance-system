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
      sql = "select * from users where username = '{}';".format(username)
      result = cur.execute(sql)
      result = cur.fetchall()             
            
      if len(result) > 0 :             
         password = result[0]['pwd']         
         user_id = result[0]['id']

         is_admin = 'Y' if result[0]['usertype'] == 'A' else 'N'          
         is_student = 'Y' if result[0]['usertype'] == 'S' else 'N'          
         is_teacher = 'Y' if result[0]['usertype'] == 'T' else 'N'          
         
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

            return redirect(url_for('home_page'))               
         else :            
            flash("Invalid Login", 'alert-danger')                  
            return render_template('login.html')            
      else :   
         # flash("User Name Not Found", 'alert-danger')                  
         return render_template('login.html')
      
   return render_template('login.html')

@app.route('/logout')
def logout():
   session.clear()
   return redirect(url_for('login'))   

@app.route('/users')
@is_logged_in
def users():    
   # Create cursor
   cur = db.connection.cursor() 

   # Get System Users
   cur.execute("SET @row_number = 0;")               
   result = cur.execute("select (@row_number:=@row_number + 1) AS row_num, users.* from users")
   usersData = cur.fetchall()   

   userTypeCombo = {'A': 'Admin', 'S':'Student', 'T':'Teacher'}
   yearsCombo = {1: 'Prep', 2:'Y1', 3:'Y2', 4:'Y3', 5:'Y4'}
   
   # [{id:1, name:'Prep'}, {id:2, name:'Y1'}, {id:3, name:'Y2'}, {id:4, name:'Y3'}, {id:5, name:'Y4'}]

   result = cur.execute("select id, id as name from schedule")
   schData = cur.fetchall() 

   return render_template('users.html', title = "users", usersData = usersData, userTypeCombo= userTypeCombo, schData=schData, yearsCombo=yearsCombo)

@app.route('/save_users', methods=['GET', 'POST'])
@is_logged_in
def save_users():    
   # Create cursor
   cur = db.connection.cursor()      

   #Storing Data into variables
   id = request.form.getlist('id')
   name = request.form.getlist('name')    
   username = request.form.getlist('username')  
   password = request.form.getlist('password') 
   email = request.form.getlist('email') 
   usertype = request.files.getlist('usertype')  
   schedule = request.form.getlist('sch') 
   picture = request.files.getlist('pciture') 

   #Getting lenght of a required value list
   listLength = len(id)
   
   if listLength > 1:         
      for x in range (0, listLength):       
               
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
                  insert into users (id, username, pwd, name, email, notes, sch_id, year, pciture, usertype)
                  values ({id}, '{username[x]}' , '{password[x]}', '{nvl(name[x])}', '{nvl(email[x])}', '{notes[x]}', {schedule[x]}, {year[x]}, "{absolute_path}");      
                  """               
         else:
            sql = f"""
                  update 
                     users
                  set 
                      username = '{username[x]}',
                      name = '{name[x]}',
                      pwd = '{password[x]}',
                      email = {nvl(email[x])},
                      notes = {nvl(notes[x])},
                      sch_id = {nvl(schedule[x])},
                      year = {nvl(year[x])},
                      usertype = {nvl(usertype[x])},
                      picture = "{absolute_path}",
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
                  insert into users (id, username, pwd, name, email, notes, sch_id, year, pciture, usertype)
                  values ({id}, '{username[0]}' , '{password[0]}', '{nvl(name[0])}', '{nvl(email[0])}', '{notes[0]}', {schedule[0]}, {year[0]}, "{absolute_path}");       
               """             
      else :   
            sql = f"""
                  update 
                     users
                  set 
                      username = '{username[0]}',
                      name = '{name[0]}',
                      pwd = '{password[0]}',
                      email = {nvl(email[0])},
                      notes = {nvl(notes[0])},
                      sch_id = {nvl(schedule[0])},
                      year = {nvl(year[0])},
                      usertype = {nvl(usertype[0])},
                      picture = "{absolute_path}",
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

@app.route('/del_user/<int:userID>')
@is_logged_in
def del_user(userID):    
   # Create cursor
   cur = db.connection.cursor() 

   sql = f"delete from users where id = {userID}"
   cur.execute(sql)
   db.connection.commit()        

   # sql = f"delete from students where class_id = {classID}"
   # cur.execute(sql)
   # db.connection.commit()        

   # sql = f"delete from classes where id = {classID}"
   # cur.execute(sql)
   # db.connection.commit()        
      
   return redirect(url_for('users'))   

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


   