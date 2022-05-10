import os
from app import app, con
from flask import Flask, jsonify,session, render_template, request, redirect, url_for,flash,make_response, Response,send_from_directory
from datetime import datetime

def fetchQuery(query):
   con.begin()

   cursor = con.cursor()
   cursor.execute(query);
   res = cursor.fetchone()

   con.close()   

   return res
   

# Default route is home page
@app.route('/')

@app.route('/home')
def home_page():  

   res = fetchQuery("select * from system_users")
   return render_template('login.html', title = "home page", res=res)