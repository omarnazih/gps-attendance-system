from app import app
from OpenSSL import SSL
from flask_sslify import SSLify
# if __name__ == '__main__':
#   app.run(debug=True, host='0.0.0.0')
#For HTTPS

if __name__ == "__main__":  
    app.run(host='0.0.0.0',ssl_context=("cert.pem", "key.pem"))
# if __name__ == '__main__':  
#     app.run('0.0.0.0', debug=True, port=8100, ssl_context='adhoc') 

# context = SSL.Context(SSL.PROTOCOL_TLS_SERVER)
# context.use_privatekey_file('key.pem')
# context.use_certificate_file('cert.pem')  
# if __name__ == '__main__':  
#      app.run(host='127.0.0.1', debug=True, ssl_context=context)
# context = SSL.Context(SSL.SSLv2_METHOD)
# context.use_certificate_file('cert.pem')
# context.use_privatekey_file('key.pem')

# if __name__ == "__main__":
#     app.run(port=1337, debug=True, ssl_context=context)
# if __name__ == "__main__":
#     app.run(debug=True, ssl_context='adhoc')

# context = ('web.crt', 'web.key')
# sslify = SSLify(app)
# if __name__ == "__main__":
#     context = ('cert.pem', 'key.pem')
#     app.run( debug = True, ssl_context = context)

# if __name__ == "__main__":
#     app.run(ssl_context=('cert.pem', 'key.pem'),host='0.0.0.0', port=8080)    

# To be able to use the over all the network
# if __name__ == '__main__':
#     app.run(debug = True, host='0.0.0.0', port=5000)  