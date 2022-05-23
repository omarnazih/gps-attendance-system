import os
import sqlalchemy
from flask import Flask
from flask_mysqldb import MySQL
from app import env

app = Flask(__name__)

app.secret_key = '>*=Tkrfqp:292KJ7'

# No Cashing
app.config["CACHE_TYPE"] = "null"
app.config['SESSION_TYPE'] = 'filesystem'

# App Configrations
app.config['UPLOAD_FOLDER']='app/uploader/'
app.config['IMAGES_FOLDER']='app/images/'
app.config['TEMPLATES']='app/templates/'
app.config['UPLOAD_IMAGE']='app/static/img/'
app.config['MAX_CONTENT_PATH']=5*1024*1024

app.config['MYSQL_USER'] = 'atsys'
app.config['MYSQL_PASSWORD'] = 'atsys'
app.config['MYSQL_DB'] = 'attendancedb'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

# def init_connection_engine():
#     pool = sqlalchemy.create_engine(
#         sqlalchemy.engine.url.URL(
#             drivername="mysql",
#             username=os.environ.get('MYSQL_USER'), #username
#             password=os.environ.get('MYSQL_PASSWORD'), #password
#             database=os.environ.get('MYSQL_DB'), #database name
#             host=os.environ.get('MYSQL_HOST') #ip
#         )
#     )
#     return pool

# bcrypt = Bcrypt()
# Cursor
db = mysql
# db = init_connection_engine()

# bcrypt.init_app(app)
from app import routes
