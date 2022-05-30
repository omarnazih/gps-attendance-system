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
   result = cur.execute("select * from modules")
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
   yearsCombo = ({'id': 1, 'name': 'Prep'}, {'id': 2, 'name': 'Y1'}, {'id': 3, 'name': 'Y2'}, {'id': 4, 'name': 'Y3'}, {'id': 5, 'name': 'Y4'})    
      
   result = cur.execute("select id, id as name from schedule")
   schData = cur.fetchall()       

   return render_template('users.html', title = "users", usersData = usersData, userTypeCombo= userTypeCombo, schData=schData, yearsCombo=yearsCombo)


@app.route('/user_edit', defaults={'user_id':None})
@app.route('/user_edit/<int:user_id>')
@is_logged_in
def user_edit(user_id):    
   # Create cursor
   cur = db.connection.cursor() 

   usersData = []
   # Get System Users   
   if user_id != None :
      result = cur.execute(f"select users.* from users where id = {user_id}")
      usersData = cur.fetchall()   

   userTypeCombo = {'A': 'Admin', 'S':'Student', 'T':'Teacher'}
   yearsCombo = {1: 'Prep', 2:'Y1', 3:'Y2', 4:'Y3', 5:'Y4'}
      
   result = cur.execute("select id, id as name from schedule")
   schData = cur.fetchall() 

   return render_template('useredit.html', title = "User Edit", usersData = usersData, userTypeCombo= userTypeCombo, schData=schData, yearsCombo=yearsCombo)

@app.route('/save_users', methods=['GET', 'POST'])
@is_logged_in
def save_users():    
   # Create cursor
   cur = db.connection.cursor()      

   #Storing Data into variables
   id = request.form.get('id')
   name = request.form.get('name')    
   username = request.form.get('username')  
   password = request.form.get('password') 
   email = request.form.get('email') 
   usertype = request.form.get('usertype')  
   year = request.form.get('year')  
   notes = request.form.get('notes')  
   schedule = request.form.get('sch') 
   old_pic = request.form.get('old_pic') 
   
   picture = request.files.get('picture') 

   print(picture)
   if picture:
      file_name = secure_filename(picture.filename);                      
   else :
      file_name = ''   
     
   # If The path is correct then save      
   if file_name != '': 
      absolute_path = os.path.abspath(app.config['IMAGES_FOLDER'] + file_name)               
      picture.save(absolute_path) 
      absolute_path = absolute_path.replace('\\','\\\\')
   elif old_pic != '':
      absolute_path = old_pic
      absolute_path = absolute_path.replace('\\','\\\\')
   else :
      absolute_path = ''
   

   if id == '':
      cur.execute("select IFNULL(max(id),0)+1 as id from users")
      res = cur.fetchone()        
      id = res['id']                        

      sql = f"""
            insert into users (id, username, pwd, name, email, notes, sch_id, year, usertype, picture)
            values ({id}, '{username}' , '{password}', '{name}', '{email}', '{notes}', {nvl(schedule)}, {nvl(year)}, {nvl(usertype)}, '{absolute_path}');      
            """               
   else:
      sql = f"""
            update 
               users
            set 
                  username = '{username}',
                  name = '{name}',
                  pwd = '{password}',
                  email = '{email}',
                  notes = '{notes}',
                  sch_id = {nvl(schedule)},
                  year = {nvl(year)},
                  usertype = {nvl(usertype)},
                  picture = '{absolute_path}'
            where 
               id = {id};      
            """     
                        
   result = cur.execute(sql)      
   db.connection.commit()    

   # FeedBack    
   flash('Data Updated Successfully', 'alert-success')                        

   return redirect(url_for('user_edit', user_id=id))

@app.route('/del_user/<int:userID>')
@is_logged_in
def del_user(userID):    
   # Create cursor
   cur = db.connection.cursor() 

   sql = f"delete from users where id = {userID}"
   cur.execute(sql)
   db.connection.commit()             

   flash("Data Deleted Successfully", "alert-success")      
      
   return redirect(url_for('users'))   

@app.route('/classes')
@is_logged_in
def classes():    
   # Create cursor
   cur = db.connection.cursor() 

   # Get System Users
   cur.execute("SET @row_number = 0;")               
   result = cur.execute("select (@row_number:=@row_number + 1) AS row_num, modules.* from modules")
   classData = cur.fetchall()   

   yearsCombo = {1: 'Prep', 2:'Y1', 3:'Y2', 4:'Y3', 5:'Y4'}   

   result = cur.execute("select id, name from majors")
   majorsCombo = cur.fetchall()      

   return render_template('classes.html', title = "Modules", classData = classData, yearsCombo= yearsCombo, majorsCombo=majorsCombo )

@app.route('/del_class/<int:classID>')
@is_logged_in
def delete_class(classID):    
   # Create cursor
   cur = db.connection.cursor() 

   sql = f"delete from attendance where module_id = {classID}"
   cur.execute(sql)
   db.connection.commit()        
     
   sql = f"delete from modules where id = {classID}"
   cur.execute(sql)
   db.connection.commit()        

   sql = f"select * from modules"
   classData = cur.execute(sql)

   flash("Data updated Successfully", "alert-success")   
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
   major = request.form.getlist('major')    

   #Getting lenght of a required value list
   listLength = len(id)

   if listLength > 1:    
      for x in range (0, listLength):                                            
         if id[x] == '':
            cur.execute("select IFNULL(max(id),0)+1 as id from modules")
            res = cur.fetchone()        
            id = res['id']                        
            
            sql = f"""
                  insert into modules (id, code, name, description, major_id)
                  values ({id}, '{code[x]}' , '{name[x]}', '{desc[x]}', {ifEmpty(major[x], 'null')});      
                  """               
         else:
            sql = f"""
                  update 
                     modules
                  set 
                      code = '{code[x]}',
                      name = '{name[x]}',
                      description = '{desc[x]}',
                      major_id = {nvl(major[x])}
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
         cur.execute("select IFNULL(max(id),0)+1 as id from modules")
         res = cur.fetchone()        
         id = res['id']                     
         sql = f"""
               insert into modules (id, code, name, description, major_id)
               values ({id}, '{code[0]}' , '{name[0]}', '{desc[0]}', {ifEmpty(major[0], 'null')});      
               """             
      else :   
            sql = f"""
                  update 
                     modules
                  set 
                      code = '{code[0]}', 
                      name = '{name[0]}',
                      description ='{desc[0]}',
                      major_id = {nvl(major[0])}                                  
                  where 
                     id = {id[0]};
                  """        
      result = cur.execute(sql)      
      db.connection.commit()          
      flash('Data Updated Successfully', 'alert-success')                     
   else :    
      flash('Please Add At least one record before saving ', 'alert-info') 

   return redirect(url_for('classes'))   

@app.route('/halls')
@is_logged_in
def halls():    
   # Create cursor
   cur = db.connection.cursor() 

   # Get System Users
   cur.execute("SET @row_number = 0;")               
   result = cur.execute("select (@row_number:=@row_number + 1) AS row_num, halls.* from halls")
   hallsData = cur.fetchall()   
   
   return render_template('halls.html', title = "Halls", hallsData = hallsData)


@app.route('/del_hall/<int:hallID>')
@is_logged_in
def delete_hall(hallID):    
   # Create cursor
   cur = db.connection.cursor() 

   sql = f"delete from halls where id = {hallID}"
   cur.execute(sql)
   db.connection.commit()        

   flash("Data updated Successfully", "alert-success")   
   return redirect(url_for('halls'))     

@app.route('/save_hall', methods=['GET', 'POST'])
@is_logged_in
def save_hall():    
   # Create cursor
   cur = db.connection.cursor()      

   #Storing Data into variables
   id = request.form.getlist('id')
   # code = request.form.getlist('code')    
   name = request.form.getlist('name')     
   lat = request.form.getlist('lat')  
   lang = request.form.getlist('lang')  

   #Getting lenght of a required value list
   listLength = len(id)

   if listLength > 1:    
      for x in range (0, listLength):                                            
         if id[x] == '':
            cur.execute("select IFNULL(max(id),0)+1 as id from halls")
            res = cur.fetchone()        
            id = res['id']                        
            
            sql = f"""
                  insert into halls (id, name, loc_lat, loc_lang)
                  values ({id}, '{name[x]}', '{lat[x]}', {lang[x]});      
                  """               
         else:
            sql = f"""
                  update 
                     halls
                  set 
                      name = '{name[x]}',
                      loc_lat = '{lat[x]}',
                      loc_lang = '{lang[x]}'                      
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
         cur.execute("select IFNULL(max(id),0)+1 as id from modules")
         res = cur.fetchone()        
         id = res['id']                     
         sql = f"""
               insert into halls (id, name, loc_lat, loc_lang)
               values ({id}, '{name[0]}', '{lat[0]}', {lang[0]});      
               """             
      else :   
            sql = f"""
                  update 
                     halls
                  set                   
                      name = '{name[0]}',
                      loc_lat = '{lat[0]}',
                      loc_lang = '{lang[0]}'                      
                  where 
                     id = {id[0]}; 
                  """        
      result = cur.execute(sql)      
      db.connection.commit()          
      flash('Data Updated Successfully', 'alert-success')                     
   else :    
      flash('Please Add At least one record before saving ', 'alert-info') 

   return redirect(url_for('halls'))     

@app.route('/takeattendance/<string:classID>', methods=['GET', 'POST'])
@is_logged_in
def take_attendance(classID):   
   # Create cursor
   cur = db.connection.cursor() 

   if request.method == 'GET':

      # Get Data
      sql = "select * from modules where id = '{}';".format(classID)
      result = cur.execute(sql)
      classData = cur.fetchone()  

      return render_template('take_attendance.html', title = "Take Attendance", classData = classData)

   elif request.method == 'POST' and session['is_student'] == 'Y' :
      print("I'm ")
      CurrentDate=datetime.date.today()  
           
      user_id = session['user_id']

      cur.execute("select IFNULL(max(id),0)+1 as id from attendance")
      res = cur.fetchone()        
      attendance_id = res['id']
      
      cur.execute(f"select 1 as val from attendance where date = '{CurrentDate}' and user_id = {user_id} and module_id= {classID}")
      res = cur.fetchone() 

      if res == None:          
         # Insert Data
         sql = """
               insert into attendance (id, date, user_id, module_id)
               values ({}, '{}' , {}, {});      
               """.format(attendance_id, CurrentDate, user_id, classID)
               
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

   cur.execute(f"select picture from users where id = {session['user_id']}")
   picPath = cur.fetchone()

   res = checkSamePerson(picPath['picture'], image, 'Y')
      
   sql = "select * from modules where id = '{}';".format(classID)
   result = cur.execute(sql)
   classData = cur.fetchone()  

   # sql = "select * from schedule where class_id = '{}' and hall_id={};".format(classID, classID)
   sql = "select * from halls where id = {};".format(1)
   result = cur.execute(sql)
   locationData = cur.fetchone()     

   if res == True:
      return jsonify(isSamePerson="True", classData = classData, locationData=locationData) 
   else :
      return jsonify(isSamePerson="False", classData = classData, locationData=locationData) 


   