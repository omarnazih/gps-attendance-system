import os
from app import app, db
from flask import Flask, jsonify,session, render_template, request, redirect, url_for,flash,make_response, Response,send_from_directory
from datetime import datetime

def fetchQuery(query):
   conn = db.connect()             
   sql = query
   result = conn.execute(sql).fetchall()  
   print(result)
   return result
# Default route is home page
@app.route('/')

@app.route('/home')
def home_page():  
   res = fetchQuery("select * from system_users")   
   return render_template('login.html', title = "home page", res=res)