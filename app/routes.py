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
   
   now = datetime.datetime.now()
   dayName = now.strftime("%A")
   print(now.strftime("%A"))   

   hoursMinutes = f"{now.hour}:{now.minute}"

   print(hoursMinutes)

   sql = f"""
            select module.*, sch.hall_id 
            from schedule sch, modules module
            where sch.module_id = module.id
            and lower(sch.day) like lower('{dayName}')
            and TIME(sch.time_from) < TIME('{hoursMinutes}')
            and TIME(sch.time_to) > TIME('{hoursMinutes}');      
         """
   cur.execute(sql)
   classData = cur.fetchall()     

   print(classData)     
      
   #TODO : Get only right modules
 
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

   return render_template('useredit.html', title = "User Edit", usersData = usersData, userTypeCombo= userTypeCombo, grpData=grpData, yearsCombo=yearsCombo)

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
            insert into users (id, username, pwd, name, email, notes, grp_id, year, usertype, picture)
            values ({id}, '{username}' , '{password}', '{name}', '{email}', '{notes}', {nvl(grp)}, {nvl(year)}, '{nvl(usertype)}', '{absolute_path}');      
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
         select (@row_number:=@row_number + 1) AS row_num, sch.id, grp.name grpname, grp.id grp_id, sch.major_id as major_id, major.name as major_name,
         case 
         when sch.year = 1 then 'Prep'
         when sch.year = 2 then 'Y1'
         when sch.year = 3 then 'Y2'
         when sch.year = 4 then 'Y3'
         when sch.year = 5 then 'Y4'
         else ''
         end as year , sch.year as year_id        
         from schedule sch, sch_groups grp, majors major
         where sch.grp_id = grp.id
         and sch.major_id = major.id
         group by grp.name, year, major.name;      
        """            
   result = cur.execute(sql)
   data = cur.fetchall()                

   return render_template('schedule.html', title = "Schedule", data = data)


@app.route('/sch_edit', defaults={'grp_id':None, 'year': None, 'major_id': None})
@app.route('/sch_edit/<int:grp_id>',defaults={'year': None, 'major_id': None})
@app.route('/sch_edit/<int:grp_id>/<int:year>',defaults={'major_id': None})
@app.route('/sch_edit/<int:grp_id>/<int:year>/<int:major_id>')
@is_logged_in
def sch_edit(grp_id, year, major_id):    
   # Create cursor
   cur = db.connection.cursor() 

   data = []
   # Get System Users   
   if grp_id != None :
      result = cur.execute(f"select schedule.* from schedule where grp_id = {grp_id} and year = {year} and major_id = {major_id} LIMIT 1")
      data = cur.fetchall()   

   yearsCombo = ({'id': '', 'name': ''},{'id': 1, 'name': 'Prep'}, {'id': 2, 'name': 'Y1'}, {'id': 3, 'name': 'Y2'}, {'id': 4, 'name': 'Y3'}, {'id': 5, 'name': 'Y4'}) 
      
   cur.execute("""select null as id, '' as name 
                  from dual 
                  union all
                  select id , name 
                  from sch_groups""")
   grpCombo = cur.fetchall() 

   cur.execute("""select null as id, '' as name 
                  from dual 
                  union all 
                  select id, name
                  from majors""")
   majorCombo = cur.fetchall() 
   
   if major_id:
      cur.execute(f"""select '' as id, '' as name 
                     from dual 
                     union all
                     select id, name
                     from modules
                     where major_id = {major_id}""")
      moduleCombo = cur.fetchall() 
   else :
      cur.execute(f"""select '' as id, '' as name 
                     from dual 
                     union all
                     select id, name
                     from modules
                     """)
      moduleCombo = cur.fetchall()          

   cur.execute("""select '' as id, '' as name 
                  from dual 
                  union all
                  select id, name
                  from halls""")
   hallCombo = cur.fetchall() 

   return render_template('schedit.html', title = "Schedule", data = data, yearsCombo=yearsCombo, grpCombo=grpCombo, majorCombo=majorCombo, moduleCombo=moduleCombo, hallCombo=hallCombo)

@app.route('/save_sch', methods=['GET', 'POST'])
@is_logged_in
def save_sch():    
   # Create cursor
   cur = db.connection.cursor()      

   #Storing Data into variables
   id = request.form.get('id')
   major = request.form.get('major')    
   year = request.form.get('year')  
   grp = request.form.get('grp') 

   # sat
   module_sat_s1 = request.form.get('module_sat_s1') 
   module_sat_s2 = request.form.get('module_sat_s2')  
   module_sat_s3 = request.form.get('module_sat_s3')  
   module_sat_s4 = request.form.get('module_sat_s4')  
   module_sat_s5 = request.form.get('module_sat_s5') 
   module_sat_s6 = request.form.get('module_sat_s6')

   # Sat Halls
   module_sat_s1_hall = request.form.get('module_sat_s1_hall') 
   module_sat_s2_hall = request.form.get('module_sat_s2_hall')  
   module_sat_s3_hall = request.form.get('module_sat_s3_hall')  
   module_sat_s4_hall = request.form.get('module_sat_s4_hall')  
   module_sat_s5_hall = request.form.get('module_sat_s5_hall') 
   module_sat_s6_hall = request.form.get('module_sat_s6_hall')

   satList = (
            {'mod':module_sat_s1, 'from': '9:00', 'to': '9:50', 'hall': module_sat_s1_hall},
            {'mod':module_sat_s2, 'from': '10:00', 'to': '10:50', 'hall': module_sat_s2_hall},
            {'mod':module_sat_s3, 'from': '11:00', 'to': '11:50', 'hall': module_sat_s3_hall},
            {'mod':module_sat_s4, 'from': '12:00', 'to': '12:50', 'hall': module_sat_s4_hall},
            {'mod':module_sat_s5, 'from': '13:00', 'to': '13:50', 'hall': module_sat_s5_hall},
            {'mod':module_sat_s6, 'from': '14:00', 'to': '14:50', 'hall': module_sat_s6_hall},
            )   

   # sun
   module_sun_s1 = request.form.get('module_sun_s1')
   module_sun_s2 = request.form.get('module_sun_s2')
   module_sun_s3 = request.form.get('module_sun_s3')
   module_sun_s4 = request.form.get('module_sun_s4')
   module_sun_s5 = request.form.get('module_sun_s5')
   module_sun_s6 = request.form.get('module_sun_s6')

   # Sun Halls
   module_sun_s1_hall = request.form.get('module_sun_s1_hall')
   module_sun_s2_hall = request.form.get('module_sun_s2_hall')
   module_sun_s3_hall = request.form.get('module_sun_s3_hall')
   module_sun_s4_hall = request.form.get('module_sun_s4_hall')
   module_sun_s5_hall = request.form.get('module_sun_s5_hall')
   module_sun_s6_hall = request.form.get('module_sun_s6_hall')

   sunList = (
            {'mod':module_sun_s1, 'from': '9:00', 'to': '9:50', 'hall': module_sun_s1_hall},
            {'mod':module_sun_s2, 'from': '10:00', 'to': '10:50', 'hall': module_sun_s2_hall},
            {'mod':module_sun_s3, 'from': '11:00', 'to': '11:50', 'hall': module_sun_s3_hall},
            {'mod':module_sun_s4, 'from': '12:00', 'to': '12:50', 'hall': module_sun_s4_hall},
            {'mod':module_sun_s5, 'from': '13:00', 'to': '13:50', 'hall': module_sun_s5_hall},
            {'mod':module_sun_s6, 'from': '14:00', 'to': '14:50', 'hall': module_sun_s6_hall},
            ) 

   # mon
   module_mon_s1 = request.form.get('module_mon_s1')
   module_mon_s2 = request.form.get('module_mon_s2')
   module_mon_s3 = request.form.get('module_mon_s3')
   module_mon_s4 = request.form.get('module_mon_s4')
   module_mon_s5 = request.form.get('module_mon_s5')
   module_mon_s6 = request.form.get('module_mon_s6')

   # mon Halls
   module_mon_s1_hall = request.form.get('module_mon_s1_hall')
   module_mon_s2_hall = request.form.get('module_mon_s2_hall')
   module_mon_s3_hall = request.form.get('module_mon_s3_hall')
   module_mon_s4_hall = request.form.get('module_mon_s4_hall')
   module_mon_s5_hall = request.form.get('module_mon_s5_hall')
   module_mon_s6_hall = request.form.get('module_mon_s6_hall')
   
   monList = (
            {'mod':module_mon_s1, 'from': '9:00', 'to': '9:50', 'hall': module_mon_s1_hall},
            {'mod':module_mon_s2, 'from': '10:00', 'to': '10:50', 'hall': module_mon_s2_hall},
            {'mod':module_mon_s3, 'from': '11:00', 'to': '11:50', 'hall': module_mon_s3_hall},
            {'mod':module_mon_s4, 'from': '12:00', 'to': '12:50', 'hall': module_mon_s4_hall},
            {'mod':module_mon_s5, 'from': '13:00', 'to': '13:50', 'hall': module_mon_s5_hall},
            {'mod':module_mon_s6, 'from': '14:00', 'to': '14:50', 'hall': module_mon_s6_hall},
            ) 

   # tue
   module_tue_s1 = request.form.get('module_tue_s1')
   module_tue_s2 = request.form.get('module_tue_s2')
   module_tue_s3 = request.form.get('module_tue_s3')
   module_tue_s4 = request.form.get('module_tue_s4')
   module_tue_s5 = request.form.get('module_tue_s5')
   module_tue_s6 = request.form.get('module_tue_s6')

   # tue Halls
   module_tue_s1_hall = request.form.get('module_tue_s1_hall')
   module_tue_s2_hall = request.form.get('module_tue_s2_hall')
   module_tue_s3_hall = request.form.get('module_tue_s3_hall')
   module_tue_s4_hall = request.form.get('module_tue_s4_hall')
   module_tue_s5_hall = request.form.get('module_tue_s5_hall')
   module_tue_s6_hall = request.form.get('module_tue_s6_hall')   

   tueList = (
            {'mod':module_tue_s1, 'from': '9:00', 'to': '9:50', 'hall': module_tue_s1_hall},
            {'mod':module_tue_s2, 'from': '10:00', 'to': '10:50', 'hall': module_tue_s2_hall},
            {'mod':module_tue_s3, 'from': '11:00', 'to': '11:50', 'hall': module_tue_s3_hall},
            {'mod':module_tue_s4, 'from': '12:00', 'to': '12:50', 'hall': module_tue_s4_hall},
            {'mod':module_tue_s5, 'from': '13:00', 'to': '13:50', 'hall': module_tue_s5_hall},
            {'mod':module_tue_s6, 'from': '14:00', 'to': '14:50', 'hall': module_tue_s6_hall},
            )  

   # tue
   module_wed_s1 = request.form.get('module_wed_s1')
   module_wed_s2 = request.form.get('module_wed_s2')
   module_wed_s3 = request.form.get('module_wed_s3')
   module_wed_s4 = request.form.get('module_wed_s4')
   module_wed_s5 = request.form.get('module_wed_s5')
   module_wed_s6 = request.form.get('module_wed_s6')

   # wed Halls
   module_wed_s1_hall = request.form.get('module_wed_s1_hall')
   module_wed_s2_hall = request.form.get('module_wed_s2_hall')
   module_wed_s3_hall = request.form.get('module_wed_s3_hall')
   module_wed_s4_hall = request.form.get('module_wed_s4_hall')
   module_wed_s5_hall = request.form.get('module_wed_s5_hall')
   module_wed_s6_hall = request.form.get('module_wed_s6_hall')    

   wedList = (
            {'mod':module_wed_s1, 'from': '9:00', 'to': '9:50', 'hall': module_wed_s1_hall},
            {'mod':module_wed_s2, 'from': '10:00', 'to': '10:50', 'hall': module_wed_s2_hall},
            {'mod':module_wed_s3, 'from': '11:00', 'to': '11:50', 'hall': module_wed_s3_hall},
            {'mod':module_wed_s4, 'from': '12:00', 'to': '12:50', 'hall': module_wed_s4_hall},
            {'mod':module_wed_s5, 'from': '13:00', 'to': '13:50', 'hall': module_wed_s5_hall},
            {'mod':module_wed_s6, 'from': '14:00', 'to': '14:50', 'hall': module_wed_s6_hall},
            )  

   # thur
   module_thur_s1 = request.form.get('module_thur_s1')
   module_thur_s2 = request.form.get('module_thur_s2')
   module_thur_s3 = request.form.get('module_thur_s3')
   module_thur_s4 = request.form.get('module_thur_s4')
   module_thur_s5 = request.form.get('module_thur_s5')
   module_thur_s6 = request.form.get('module_thur_s6')                

   # tue Halls
   module_thur_s1_hall = request.form.get('module_thur_s1_hall')
   module_thur_s2_hall = request.form.get('module_thur_s2_hall')
   module_thur_s3_hall = request.form.get('module_thur_s3_hall')
   module_thur_s4_hall = request.form.get('module_thur_s4_hall')
   module_thur_s5_hall = request.form.get('module_thur_s5_hall')
   module_thur_s6_hall = request.form.get('module_thur_s6_hall')    

   thurList = (
            {'mod':module_thur_s1, 'from': '9:00', 'to': '9:50', 'hall': module_thur_s1_hall},
            {'mod':module_thur_s2, 'from': '10:00', 'to': '10:50', 'hall': module_thur_s2_hall},
            {'mod':module_thur_s3, 'from': '11:00', 'to': '11:50', 'hall': module_thur_s3_hall},
            {'mod':module_thur_s4, 'from': '12:00', 'to': '12:50', 'hall': module_thur_s4_hall},
            {'mod':module_thur_s5, 'from': '13:00', 'to': '13:50', 'hall': module_thur_s5_hall},
            {'mod':module_thur_s6, 'from': '14:00', 'to': '14:50', 'hall': module_thur_s6_hall},
            )   

   if id == '':                      
      for elm in satList :
         day = 'Saturday'
         # Creating Next ID
         cur.execute("select IFNULL(max(id),0)+1 as id from schedule")
         res = cur.fetchone()        
         id = res['id']    

         sql = f"""
               insert into schedule 
                  (`id`,
                  `hall_id`,
                  `module_id`,
                  `day`,
                  `time_from`,
                  `time_to`,
                  `grp_id`,
                  `year`,
                  `major_id`)
               values 
                  ({id}, {nvl(elm['hall'])} , {nvl(elm['mod'])}, '{day}', '{elm['from']}', '{elm['to']}', {nvl(grp)}, {nvl(year)}, {nvl(major)});      
               """ 
         result = cur.execute(sql)      
         db.connection.commit()     

      for elm in sunList :
         day = 'Sunday'
         # Creating Next ID
         cur.execute("select IFNULL(max(id),0)+1 as id from schedule")
         res = cur.fetchone()        
         id = res['id']    

         sql = f"""
               insert into schedule 
                  (`id`,
                  `hall_id`,
                  `module_id`,
                  `day`,
                  `time_from`,
                  `time_to`,
                  `grp_id`,
                  `year`,
                  `major_id`)
               values 
                  ({id}, {nvl(elm['hall'])} , {nvl(elm['mod'])}, '{day}', '{elm['from']}', '{elm['to']}', {nvl(grp)}, {nvl(year)}, {nvl(major)});      
               """ 
         result = cur.execute(sql)      
         db.connection.commit()                                 
   else:
      for elm in satList :   
         day = 'Saturday'   
         sql = f"""   
               update 
                  schedule
               set 
                     hall_id = {nvl(elm['hall'])},
                     module_id = {nvl(elm['mod'])},
                     day = '{day}',
                     time_from = '{elm['from']}',
                     time_to = '{elm['to']}',
                     grp_id = {nvl(grp)},
                     year = {nvl(year)},
                     major_id = {nvl(major)}
               where 
                  id = {id};      
               """   
         print(sql)      
         result = cur.execute(sql)      
         db.connection.commit()   

      for elm in sunList :   
         day = 'Sunday'   
         sql = f"""   
               update 
                  schedule
               set 
                     hall_id = {nvl(elm['hall'])},
                     module_id = {nvl(elm['mod'])},
                     day = '{day}',
                     time_from = '{elm['from']}',
                     time_to = '{elm['to']}',
                     grp_id = {nvl(grp)},
                     year = {nvl(year)},
                     major_id = {nvl(major)}
               where 
                  id = {id};
               """   
         print(sql)      
         result = cur.execute(sql)      
         db.connection.commit()           
                        
   # FeedBack    
   flash('Data Updated Successfully', 'alert-success')                        

   return redirect(url_for('sch_edit', grp_id=grp, year=year, major_id=major ))

@app.route('/del_sch/<int:grp_id>/<int:year>/<int:major_id>' , methods=['POST', 'GET'])
@is_logged_in
def del_sch(grp_id, year, major_id):    
   # Create cursor
   cur = db.connection.cursor() 
   try:      
      sql = f"delete from schedule where grp_id = {grp_id} and year = {year} and major_id={major_id}"
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

   res = checkSamePerson(picPath['picture'], image, 'Y')
      
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
                  and usr.usertype = 'S' """)
   data = cur.fetchall()     
   return render_template('attendanceReport.html', title = "Attendance Report", data = data)
   