import os
from app import app
from flask import Flask, jsonify,session, render_template, request, redirect, url_for,flash,make_response, Response,send_from_directory
from datetime import datetime

# Default route is home page
@app.route('/')

@app.route('/home')
def home_page():   
   return render_template('login.html', title = "home page")