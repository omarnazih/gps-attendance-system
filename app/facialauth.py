import cv2
import numpy as np
import face_recognition
import os

def findEncodings(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList

def checkSamePerson(baseImage, newImage):

    baseImagePath = baseImage
    newImagePath = newImage
        
    baseImage = cv2.imread(baseImagePath)   
    newImage =  cv2.imread(newImagePath)  


    # Training the face recognition model
    imagesList = []
    imagesList.append(baseImage)
    encodedImage = findEncodings(imagesList)    

    imgS = cv2.resize(newImage, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    facesCurFrame = face_recognition.face_locations(imgS)
    encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

    for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):        
        matches = face_recognition.compare_faces(encodedImage, encodeFace)
        print(matches[0])
        return matches[0]
        # print(matches)
        # faceDis = face_recognition.face_distance(encodedImage, encodeFace)
        # #Printing Face Distance
        # print(faceDis)
        # matchIndex = np.argmin(faceDis)
             
# For testing
# checkSamePerson('Training_images/omar.jpg', 'Test_images/false_test.jpg')             