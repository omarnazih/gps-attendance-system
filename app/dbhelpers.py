from flask import flash, redirect, url_for
from app import db, dbhelpers

def validateSchHD(major, year, grp):
    conn = db.connection.cursor()      

    sql = f"""select 1 res from schedule_hd where major_id = {major} and year = {year} and grp_id = {grp};"""
    conn.execute(sql)     
    res = conn.fetchone()
    
    if res:
        return False
    else :
        return True

def save_sch_hd(row):
    recordId =''
    conn = db.connection.cursor()      

    if validateSchHD(row['major_id'], row['year'], row['grp_id']):

        placeholders = ', '.join(['%s'] * len(row))
        columns = ', '.join(row.keys())           

        sql = "select IFNULL(max(id),0)+1 id from schedule_hd;"
        conn.execute(sql)     
        recordId = conn.fetchone()

        row['id'] = recordId['id']
        new_hd_id = row['id']                     
        
        finalRecord = list(row.values())  
        sql = "Insert into schedule_hd ( {} ) VALUES ( {} )".format(columns, placeholders)               
    
        conn.execute(sql,finalRecord)  
        db.connection.commit()                

        print(sql )
        
        #FeedBack
        flash('Data Saved Successfully', 'alert-success')         
        conn.close() 
        return new_hd_id
    else:
        flash('Recorde Already Stored in database', 'alert-danger')         
        return

def save_sch_dt(row):
    recordId =''
    conn = db.connection.cursor()      

    placeholders = ', '.join(['%s'] * len(row))
    columns = ', '.join(row.keys())   
    
    sql = "select IFNULL(max(id),0)+1 id  from schedule;"
    conn.execute(sql)     
    recordId = conn.fetchone()

    row['id'] = recordId['id']      
    finalRecord = list(row.values())        
    
    sql = "Insert into schedule ( {} ) VALUES ( {} )".format(columns, placeholders) 
    conn.execute(sql, finalRecord)  
    db.connection.commit()                         
    
    conn.close() 

    return True
    

def update_sch_hd(row):
  
    conn = db.connection.cursor()      
    #Replacing "None" Values with with null so MySql can understand it  
    for x in row:
      if row['{}'.format(x)] == None:
        row['{}'.format(x)] = 'null'

    sql = "update schedule_hd SET major_id = {}, year = {}, grp_id = {} where id = {}".format(row['major_id'], row['year'], row['grp_id'], row['id'])
    
    conn.execute(sql)   
    db.connection.commit()       
    
    #FeedBack
    flash('Data Updated Successfully', 'alert-success')                 

    return True

def update_sch_dt(row):

    conn = db.connection.cursor()      
    #Replacing "None" Values with with null so MySql can understand it  
    for x in row:
      if row['{}'.format(x)] == None or row['{}'.format(x)] == 'None':
        row['{}'.format(x)] = 'null'

    sql = f"""update schedule SET  hall_id = {row['hall_id']}, 
                                   module_id = {row['module_id']}, 
                                   day = '{row['day']}',
                                   time_from = '{row['time_from']}',
                                   time_to = '{row['time_to']}'
                                   where id = {row['id']}"""
    
    print(sql)
    conn.execute(sql)   
    db.connection.commit()                    

    return True

def getStudentsCount():
    # Curssor
    conn = db.connection.cursor()      
    sql = f"""
        select count(id) count
        from users
        where usertype = 'S';
    """    
    conn.execute(sql)   
    res = conn.fetchone() 
    print(res['count'] )

    return res['count']  

def getTeachersCount():
    # Curssor
    conn = db.connection.cursor()      
    sql = f"""
        select count(id) count
        from users
        where usertype = 'T';
    """    
    conn.execute(sql)   
    res = conn.fetchone() 
    print(res['count'])

    return res['count']
    
def getAttendaceCount():
    # Curssor
    conn = db.connection.cursor()      
    sql = f"""
        select count(id) count
        from attendance;
    """    
    conn.execute(sql)   
    res = conn.fetchone() 
    print(res['count'] )

    return res['count'] 

def getClassesCount():
    # Curssor
    conn = db.connection.cursor()      
    sql = f"""
        select count(id) count
        from modules;
    """    
    conn.execute(sql)   
    res = conn.fetchone() 
    print(res['count'] )

    return res['count']    
