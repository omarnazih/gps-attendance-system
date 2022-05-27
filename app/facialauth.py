import cv2
import base64
import numpy as np
import io
import face_recognition
import os

def findEncodings(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList

def readb64(uri):
   encoded_data = uri.split(',')[1]
   nparr = np.fromstring(base64.b64decode(encoded_data), np.uint8)
   img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
   return img

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

    imgS = cv2.resize(newImage, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    # cv2.imshow("test", imgS)        
    # cv2.waitKey(0)   

    facesCurFrame = face_recognition.face_locations(imgS) 
    encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

    # print()
    for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):   
        matches = face_recognition.compare_faces(encodedImage, encodeFace)
        print(matches[0])
        return matches[0]
      