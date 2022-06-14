import cv2
import base64
import numpy as np
import io
import face_recognition
import os

# Train Available images for the user in the system.
def findEncodings(images):
    encodeList = []
    for img in images:
       try:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
       except:
        print("There was a problem in facetraining")
        flash("There was a proplem in face training")   

    return encodeList

# Read Base64 Images
def readb64(uri):
   encoded_data = uri.split(',')[1]
   nparr = np.fromstring(base64.b64decode(encoded_data), np.uint8)
   img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
   return img

# Checks if the sent image of a person is the same persons that we have image of him in the system.
def checkSamePerson(baseImage, newImage, isBase64='N'):
    baseImagePath = baseImage
        
    if isBase64 == 'Y':
        newImage = readb64(newImage)  
    else:
        newImagePath = newImage
        newImage =  cv2.imread(newImagePath)  

    baseImage = cv2.imread(baseImagePath)   

    # Training the face recognition model
    imagesList = []
    imagesList.append(baseImage)    
    encodedImage = findEncodings(imagesList)    

    # Resizing and converting colors to match trained model.
    imgS = cv2.resize(newImage, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    # Getting only faces from the picture.
    facesCurFrame = face_recognition.face_locations(imgS, model="cnn") 
    # Converting face image to encoded vesrion so it can be matched with uploaded user image on the system
    encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

    # Looping on both (New taken picure of user) and (uploaded one on the system)
    # and checking if the importat landmarks of the facematches or not
    for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):   
        matches = face_recognition.compare_faces(encodedImage, encodeFace)
        print(matches[0])
        return matches[0]
        # Comment