from app import app

# if __name__ == '__main__':
#   app.run(debug=True)

# To be able to use the over all the network
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  