from app import app

# HTTPS (Self Signed Cert)
# if __name__ == "__main__":
#     # To make sure site loads on HTTPS://
#     app.jinja_env.auto_reload = True
#     app.config['TEMPLATES_AUTO_RELOAD'] = True      
#     app.run(host='0.0.0.0',ssl_context=("cert.pem", "key.pem"))

# HTTP 
if __name__ == '__main__':
    app.run(debug = True,port=5000)  