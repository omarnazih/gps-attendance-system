import os
import base64
from app import app, db
from werkzeug.utils import secure_filename
from flask import Flask, jsonify,session, render_template, request, redirect, url_for,flash,make_response, Response,send_from_directory
from functools import wraps
from app.facialauth import checkSamePerson
from app.dbhelpers import *
from app.helpersfn import *
import datetime



# Check if user logged in
# If user logged in then allow else redirect for loing!
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
   # Create cursor (through the connection we have with database)
   cur = db.connection.cursor() 
   
   dayName = getDay()   
   print(f"Day is {dayName}")   

   hoursMinutes = getTimeHM()
   print(f"Time is {hoursMinutes}")

   classData=[]
   # If user have year, major and group values then he is allowed to see attendance cards
   # else show dashboard  
   if session['year'] and session['major_id'] and session['grp_id']:
      year = session['year']
      major_id = session['major_id']
      grp_id = session['grp_id']
      sql = f"""
               select module.*, sch.hall_id 
               from schedule_hd sch_hd, schedule sch, modules module
               where sch_hd.id = sch.hd_id
               and sch.module_id = module.id
               and sch_hd.year = {year}
               and sch_hd.major_id = {major_id}
               and sch_hd.grp_id = {grp_id}
               and lower(sch.day) like lower('{dayName}')
               and TIME(sch.time_from) < TIME('{hoursMinutes}')
               and TIME(sch.time_to) > TIME('{hoursMinutes}');      
            """   
      cur.execute(sql)
      classData = cur.fetchall()     
   
   dashboardData={}
   if session['is_admin'] == 'Y' or session['is_teacher'] == 'Y':
      dashboardData = {'studentsCount': getStudentsCount(), 
                        'teachersCount': getTeachersCount(),
                        'attendanceCount': getAttendaceCount(),
                        'classesCount': getClassesCount(),
                        'emailsCount': 0,
                     }      
    
   return render_template('home.html', title = "home page", classData = classData, dashboardData=dashboardData)

@app.route('/login', methods=['GET', 'POST'])
def login():    
   if request.method == 'POST':
      # Create cursor
      cur = db.connection.cursor() 

      # Get Form Fileds (sent from form)
      username = request.form['username']
      password_candidate = request.form['password']      
      
      # Get system users data
      sql = "select * from users where username = '{}';".format(username)
      result = cur.execute(sql)
      result = cur.fetchone()             

      # Storing Session data
      if len(result) > 0 :             
         password = result['pwd']         
         user_id = result['id']
         year = result['year']
         major_id = result['major_id']
         grp_id = result['grp_id']

         is_admin = 'Y' if result['usertype'] == 'A' else 'N'          
         is_student = 'Y' if result['usertype'] == 'S' else 'N'          
         is_teacher = 'Y' if result['usertype'] == 'T' else 'N'          
         
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
            session['year'] = year 
            session['major_id'] = major_id 
            session['grp_id'] = grp_id 

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
      
   result = cur.execute("select id, id as name from schedule")
   schData = cur.fetchall()       

   return render_template('users.html', title = "users", usersData = usersData, schData=schData)

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

   userTypeCombo = ({'id': '', 'name': ''}, {'id': 'A', 'name': 'Admin'}, {'id': 'S', 'name': 'Student'}, {'id': 'T', 'name': 'Teaching staff'})
   yearsCombo = ({'id': '', 'name': ''}, {'id': 1, 'name': 'Prep'}, {'id': 2, 'name': 'Y1'}, {'id': 3, 'name': 'Y2'}, {'id': 4, 'name': 'Y3'}, {'id': 5, 'name': 'Y4'}) 
      
   cur.execute("""
                  select id, name 
                  from sch_groups""")
   grpData = cur.fetchall() 

   cur.execute("""
                  select id, name 
                  from majors""")
   majorCombo = cur.fetchall() 

   return render_template('useredit.html', title = "User Edit", usersData = usersData, userTypeCombo= userTypeCombo, grpData=grpData, yearsCombo=yearsCombo, majorCombo=majorCombo)

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
   major = request.form.get('major')  
   year = request.form.get('year')  
   notes = request.form.get('notes')  
   grp = request.form.get('grp') 
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
            insert into users (id, username, pwd, name, email, notes, grp_id, year, usertype, major_id, picture)
            values ({id}, '{username}' , '{password}', '{name}', '{email}', '{notes}', {nvl(grp)}, {nvl(year)}, '{nvl(usertype)}', '{nvl(major)}', '{absolute_path}');      
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
                  grp_id = {nvl(grp)},
                  year = {nvl(year)},
                  usertype = '{nvl(usertype)}',
                  major_id = '{nvl(major)}',
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

#!Start Schedule 
@app.route('/schedule')
@is_logged_in
def schedule():    
   # Create cursor
   cur = db.connection.cursor() 

   # Get System Users
   cur.execute("SET @row_number = 0;")   
   sql= """
            select 
               (@row_number:=@row_number + 1) AS row_num, 
               sch.id, 
               grp.name grpname, 
               grp.id grp_id, 
               major.name as major_name,
               case 
               when sch.year = 1 then 'Prep'
               when sch.year = 2 then 'Y1'
               when sch.year = 3 then 'Y2'
               when sch.year = 4 then 'Y3'
               when sch.year = 5 then 'Y4'
               else ''
               end as year, 
               sch.year as year_id        
            from 
               schedule_hd as sch
               left join sch_groups as grp
               on sch.grp_id = grp.id
               inner join majors as major
               on sch.major_id = major.id
            group by grp.name, year, major.name;     
        """            
   result = cur.execute(sql)
   data = cur.fetchall()                

   return render_template('schedule.html', title = "Schedule", data = data)

@app.route('/sch_edit/',defaults={'id': None})
@app.route('/sch_edit/<int:id>')
@is_logged_in
def sch_edit(id):    
   # Create cursor
   cur = db.connection.cursor() 

   data = []
   dt_data=[]   
   # Get System Users   
   if id != None :      
      result = cur.execute(f"select hd.* from schedule_hd hd where hd.id = {id} LIMIT 1")
      data = cur.fetchall()         
      cur.execute("SET @row_number = 0;")   
      cur.execute(f"""select (@row_number:=@row_number + 1) AS row_num, 
                     schedule.*,
                     case 
                     when schedule.time_from = '9:00' then 1
                     when schedule.time_from = '10:00' then 2
                     when schedule.time_from = '11:00' then 3
                     when schedule.time_from = '12:00' then 4
                     when schedule.time_from = '13:00' then 5
                     when schedule.time_from = '14:00' then 6
                     else ''
                     end as slot_id                     
                     from schedule where hd_id = {id} order by day""")
      dt_data = cur.fetchall()

   yearsCombo = ({'id': '', 'name': ''},{'id': 1, 'name': 'Prep'}, {'id': 2, 'name': 'Y1'}, {'id': 3, 'name': 'Y2'}, {'id': 4, 'name': 'Y3'}, {'id': 5, 'name': 'Y4'}) 

   dayCombo = ({'id': '', 'name': ''},{'id': 'Saturday', 'name': 'Saturday'}, {'id': 'Sunday', 'name': 'Sunday'}, {'id': 'Monday', 'name': 'Monday'}, {'id': 'Tuesday', 'name': 'Tuesday'}, {'id': 'Wednesday', 'name': 'Wednesday'}, {'id': 'Thursday', 'name': 'Thursday'}) 

   slotCombo = ({'id': '', 'name': ''}, {'id': '1', 'name': 'Slot1(9:00-9:50)'}, {'id': '2', 'name': 'Slot2(10:00-10:50)'},{'id': '3', 'name': 'Slot3(11:00-11:50)'}, {'id': '4', 'name': 'Slot4(12:00-12:50)'}, {'id': '5', 'name': 'Slot5(13:00-13:50)'}, {'id': '6', 'name': 'Slot6(14:00-14:50)'}) 
      
   cur.execute("""
                  select id , name 
                  from sch_groups""")
   grpCombo = cur.fetchall() 

   cur.execute(""" 
                  select id, name
                  from majors""")
   majorCombo = cur.fetchall() 

   cur.execute(f"""
                  select id, name
                  from modules
                  """)
   moduleCombo = cur.fetchall()              

   cur.execute("""
                  select id, name
                  from halls""")                  
   hallCombo = cur.fetchall() 

   print(data)
   return render_template('schedit.html', title = "Schedule", data = data, dt_data=dt_data, yearsCombo=yearsCombo, grpCombo=grpCombo, majorCombo=majorCombo, moduleCombo=moduleCombo, hallCombo=hallCombo, dayCombo=dayCombo, slotCombo=slotCombo)

@app.route('/save_sch', methods=['GET', 'POST'])
@is_logged_in
def save_sch():    
   # Create cursor
   cur = db.connection.cursor()      

   #Storing Data into variables
   hd_id = request.form.get('hd_id')
   major = request.form.get('major')    
   year = request.form.get('year')  
   grp = request.form.get('grp') 

   # Detail Data
   dt_id = request.form.getlist('dt_id')
   day = request.form.getlist('day')
   slot = request.form.getlist('slot')
   module = request.form.getlist('module')
   hall = request.form.getlist('hall')   
      
   #Getting lenght of a required value list
   listLength = len(day) 

   if major != '' or year !='' or grp !='':
      if hd_id != None:      
         row_hd={ 
         'id': hd_id,
         'major_id': int(major),
         'year': int(year),
         'grp_id': int(grp)
         } 
         update_sch_hd(row_hd)
      else :      
         row_hd={ 
         'id': ifEmpty(hd_id, None),
         'major_id': int(major),
         'year': int(year),
         'grp_id': int(grp)
         } 
         hd_id = save_sch_hd(row_hd)

      if listLength > 1 and int(hd_id) > 0:         
         for x in range (0, listLength): 
            if slot[x] == '1':
               time_from = '9:00'
               time_to = '9:55'
            elif slot[x] == '2':
               time_from = '10:00'
               time_to = '10:55'                  
            elif slot[x] == '3':
               time_from = '11:00'
               time_to = '11:55'                  
            elif slot[x] == '4':
               time_from = '12:00'
               time_to = '12:55'                  
            elif slot[x] == '5':
               time_from = '13:00'
               time_to = '13:55'                  
            elif slot[x] == '6':
               time_from = '14:00'
               time_to = '14:55'    
            else:
               time_from = ''                                      
               time_to = ''

            if x >= len(dt_id):
               row={ 
                  'id': None,
                  'hd_id': hd_id, 
                  'module_id': nvl(module[x]),
                  'day': nvl(day[x]),
                  'time_from': time_from,
                  'time_to': time_to,
                  'hall_id': nvl(hall[x])
                  }    

               save_sch_dt(row)                                          
            else:                     
               row={ 
                  'id': ifEmpty(dt_id[x], None),
                  'hd_id': hd_id, 
                  'module_id': nvl(module[x]),
                  'day': nvl(day[x]),
                  'time_from': time_from,
                  'time_to': time_to,
                  'hall_id': nvl(hall[x])
                  } 
               #If Id is null insert new user            
               if ifEmpty(dt_id[x], None) == None:
                  save_sch_dt(row)          
               else :   
                  update_sch_dt(row)   
                    
                      
      elif listLength == 1 and (hd_id != None or hd_id != ''):                   
         if slot[0] == '1':
            time_from = '9:00'
            time_to = '9:55'
         elif slot[0] == '2':
            time_from = '10:00'
            time_to = '10:55'                  
         elif slot[0] == '3':
            time_from = '11:00'
            time_to = '11:55'                  
         elif slot[0] == '4':
            time_from = '12:00'
            time_to = '12:55'                  
         elif slot[0] == '5':
            time_from = '13:00'
            time_to = '13:55'                  
         elif slot[0] == '6':
            time_from = '14:00'
            time_to = '14:55'    
         else:
            time_from = ''                                      
            time_to = '' 

         while("" in dt_id) :
            dt_id.remove('')         
         print(f"this is lngth {len(dt_id)}")
         print(dt_id)
         if len(dt_id) > 0:
            row={ 
               'id': ifEmpty(dt_id[0], None),
               'hd_id': hd_id, 
               'module_id': nvl(module[0]),
               'day': nvl(day[0]),
               'time_from': time_from,
               'time_to': time_to,
               'hall_id': nvl(hall[0])
               } 
            print("I'm here")
            update_sch_dt(row)   
         else :
            row={ 
               'id': None,
               'hd_id': hd_id, 
               'module_id': nvl(module[0]),
               'day': nvl(day[0]),
               'time_from': time_from,
               'time_to': time_to,
               'hall_id': nvl(hall[0])
               }   
            save_sch_dt(row)                                 

      else :    
         flash('Please Add At least one record before saving ', 'alert-info')                           
   else :
      flash('Please Fill Major, Year and Group', 'alert-danger')

   return redirect(url_for('sch_edit', id=hd_id))

@app.route('/del_sch/<int:id>' , methods=['POST', 'GET'])
@is_logged_in
def del_sch(id):    
   # Create cursor
   cur = db.connection.cursor() 
   try:      
      sql = f"delete from schedule where hd_id = {id}"
      cur.execute(sql)
      db.connection.commit() 

      sql = f"delete from schedule_hd where id = {id}"
      cur.execute(sql)
      db.connection.commit()               

      flash("Data updated!!", "alert-success")
      return redirect(url_for('schedule'))
   except:
      flash("Something went Wrong!!", "alert-danger")
      return redirect(url_for('schedule'))                      

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

   return render_template('classes.html', title = "Modules", classData = classData, majorsCombo=majorsCombo )

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

# Halls
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

   # cur.execute(f"select id from schedule where hall_id = {hallID}")
   # res = cur.fetchone()        
   # sch_id = res['id']  

   sql = f"update schedule set hall_id = null where hall_id = {hallID}"
   cur.execute(sql)
   db.connection.commit()        

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
   floor = request.form.getlist('floor')     
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
                  insert into halls (id, name, floor, loc_lat, loc_lang)
                  values ({id}, '{name[x]}', {floor[x]}, '{lat[x]}', {lang[x]});      
                  """               
         else:
            sql = f"""
                  update 
                     halls
                  set 
                      name = '{name[x]}',
                      floor= {floor[x]},
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
               insert into halls (id, name, floor, loc_lat, loc_lang)
               values ({id}, '{name[0]}', {floor[0]}, '{lat[0]}', {lang[0]});      
               """             
      else :   
            sql = f"""
                  update 
                     halls
                  set                   
                      name = '{name[0]}',
                      floor= {floor[x]},
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

# Majors
@app.route('/majors')
@is_logged_in
def majors():    
   # Create cursor
   cur = db.connection.cursor() 

   # Get System Users
   cur.execute("SET @row_number = 0;")               
   result = cur.execute("select (@row_number:=@row_number + 1) AS row_num, majors.* from majors")
   mainData = cur.fetchall()   
   
   return render_template('majors.html', title = "Majors", mainData = mainData)

@app.route('/del_major/<int:ID>')
@is_logged_in
def delete_major(ID):    
   # Create cursor
   cur = db.connection.cursor() 

   sql = f"update users set major_id = null where major_id = {ID}"
   cur.execute(sql)
   db.connection.commit()        

   sql = f"delete from majors where id = {ID}"
   cur.execute(sql)
   db.connection.commit()        

   flash("Data updated Successfully", "alert-success")   
   return redirect(url_for('majors'))     

@app.route('/save_major', methods=['GET', 'POST'])
@is_logged_in
def save_major():    
   # Create cursor
   cur = db.connection.cursor()      

   #Storing Data into variables
   id = request.form.getlist('id')   
   code = request.form.getlist('code')   
   name = request.form.getlist('name')     


   #Getting lenght of a required value list
   listLength = len(id)

   if listLength > 1:    
      for x in range (0, listLength):                                            
         if id[x] == '':
            cur.execute("select IFNULL(max(id),0)+1 as id from majors")
            res = cur.fetchone()        
            id = res['id']                        
            
            sql = f"""
                  insert into majors (id, name, code)
                  values ({id}, '{name[x]}', '{code[x]}');      
                  """               
         else:
            sql = f"""
                  update 
                     majors
                  set 
                      name = '{name[x]}',                  
                      code = '{code[x]}'                  
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
         cur.execute("select IFNULL(max(id),0)+1 as id from majors")
         res = cur.fetchone()        
         id = res['id']                     
         sql = f"""
               insert into majors (id, name, code)
               values ({id}, '{name[0]}', '{code[0]}');      
               """             
      else :   
            sql = f"""
                  update 
                     majors
                  set                   
                      name = '{name[0]}',
                      code = '{code[0]}'                   
                  where 
                     id = {id[0]}; 
                  """        
      result = cur.execute(sql)      
      db.connection.commit()          
      flash('Data Updated Successfully', 'alert-success')                     
   else :    
      flash('Please Add At least one record before saving ', 'alert-info') 

   return redirect(url_for('majors'))  

# Groups
@app.route('/groups')
@is_logged_in
def groups():    
   # Create cursor
   cur = db.connection.cursor() 

   # Get System Users
   cur.execute("SET @row_number = 0;")               
   result = cur.execute("select (@row_number:=@row_number + 1) AS row_num, sch_groups.* from sch_groups")
   mainData = cur.fetchall()   
   
   return render_template('groups.html', title = "Groups", mainData = mainData)

@app.route('/del_grp/<int:grpID>')
@is_logged_in
def delete_grp(grpID):    
   # Create cursor
   cur = db.connection.cursor() 

   sql = f"update schedule_hd set grp_id = null where grp_id = {grpID}"
   cur.execute(sql)
   db.connection.commit()     

   sql = f"update users set grp_id = null where grp_id = {grpID}"
   cur.execute(sql)
   db.connection.commit()        

   sql = f"delete from sch_groups where id = {grpID}"
   cur.execute(sql)
   db.connection.commit()        

   flash("Data updated Successfully", "alert-success")   
   return redirect(url_for('groups'))     

@app.route('/save_grp', methods=['GET', 'POST'])
@is_logged_in
def save_grp():    
   # Create cursor
   cur = db.connection.cursor()      

   #Storing Data into variables
   id = request.form.getlist('id')   
   name = request.form.getlist('name')     

   #Getting lenght of a required value list
   listLength = len(id)

   if listLength > 1:    
      for x in range (0, listLength):                                            
         if id[x] == '':
            cur.execute("select IFNULL(max(id),0)+1 as id from sch_groups")
            res = cur.fetchone()        
            id = res['id']                        
            
            sql = f"""
                  insert into sch_groups (id, name)
                  values ({id}, '{name[x]}');      
                  """               
         else:
            sql = f"""
                  update 
                     sch_groups
                  set 
                      name = '{name[x]}'                   
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
         cur.execute("select IFNULL(max(id),0)+1 as id from sch_groups")
         res = cur.fetchone()        
         id = res['id']                     
         sql = f"""
               insert into sch_groups (id, name)
               values ({id}, '{name[0]}');      
               """             
      else :   
            sql = f"""
                  update 
                     sch_groups
                  set                   
                      name = '{name[0]}'                  
                  where 
                     id = {id[0]}; 
                  """        
      result = cur.execute(sql)      
      db.connection.commit()          
      flash('Data Updated Successfully', 'alert-success')                     
   else :    
      flash('Please Add At least one record before saving ', 'alert-info') 

   return redirect(url_for('groups'))     

# Take attendance (receive classid and hallid as parametes to store in attendance table)
@app.route('/takeattendance/<string:classID>/<int:hallID>', methods=['GET', 'POST'])
@is_logged_in
def take_attendance(classID, hallID):   
   # Create cursor
   cur = db.connection.cursor() 

   if request.method == 'GET':
      # Get Data
      sql = "select * from modules where id = '{}';".format(classID)
      result = cur.execute(sql)
      classData = cur.fetchone()  

      return render_template('take_attendance.html', title = "Take Attendance", classData = classData, hallID=hallID)

   elif request.method == 'POST' and session['is_student'] == 'Y' :      
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
      return jsonify(response="Something went wrong!!, Please Make sure you registered as student before taking attendance")                        

# Params : image, classid, hallid
# Functionality : Validates user image through checkSamePerson() available in facialauth.py that 
# checks if the the same person or not.
# if same person it returns true and location data if not it send a message that's not the same person.
@app.route('/faceauth', methods=['GET', 'POST'])
@is_logged_in
def face_auth():   
   # Create cursor
   cur = db.connection.cursor() 

   json = request.get_json();   
   image = json['picture']
   classID = json['classIDVal']
   hallID = json['hallIDVal']
   
   cur.execute(f"select picture from users where id = {session['user_id']}")
   picPath = cur.fetchone()
   print(picPath)
   res = checkSamePerson(picPath['picture'], image, 'Y')

   print(f"this is res = {res}")   
   sql = "select * from modules where id = '{}';".format(classID)
   result = cur.execute(sql)
   classData = cur.fetchone()  

   if hallID:
      sql = "select * from halls where id = {};".format(hallID)           
      cur.execute(sql)
      locationData = cur.fetchone()    
   else :
      locationData = []    
      flash("No Hall Is Provided", "alert-danger")

   if res == True:
      return jsonify(isSamePerson="True", classData = classData, locationData=locationData) 
   else :
      print("I'm here")
      return jsonify(isSamePerson="False", classData = classData, locationData=locationData) 

@app.route('/attendancerep', methods=['GET', 'POST'])
@is_logged_in
def attendancerep():      
   # Cursor
   cur = db.connection.cursor() 
   # Set row count to 0   
   cur.execute("SET @row_number = 0;")               

   cur.execute("""select (@row_number:=@row_number + 1) AS row_num, 
                  att.date, TIME(att.time) time, usr.name username,module.name modname,
                  case 
                  when usr.year = 1 then 'Prep'
                  when usr.year = 2 then 'Y1'
                  when usr.year = 3 then 'Y2'
                  when usr.year = 4 then 'Y3'
                  when usr.year = 5 then 'Y4'
                  else ''
                  end as year                    
                  from attendance att, users usr, modules module
                  where att.user_id = usr.id
                  and att.module_id = module.id 
                  and usr.usertype = 'S'
                  """)
   data = cur.fetchall() 

   return render_template('attendanceReport.html', title = "Attendance Report", data = data)
   