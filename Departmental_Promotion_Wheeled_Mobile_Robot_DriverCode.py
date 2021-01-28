
from playsound import playsound
import numpy as np
import cv2
import os
import pygame
import pyzbar.pyzbar as pyzbar
import serial
import sys

qrcodePath = "path for your qr"
audioPath = "path for your audio"

error=["Please check UART connection",
        "Please check camera connection"]

font = cv2.FONT_HERSHEY_PLAIN
cap = cv2.VideoCapture(0 + cv2.CAP_DSHOW)
video_capture = cap
video_capture.set(3, 160)
video_capture.set(4, 120)
pygame.init()

#qr=cv2.QRCodeDetector()

def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    print(result)

def UART(direction):

    '''Serial communications: get a response'''
    try:
        serialPort = serial.Serial( port = "you port for communicate COM4 COM5 ...",
                                baudrate=115200,
                                bytesize=8, 
                                timeout=2, 
                                stopbits=serial.STOPBITS_ONE)
        serialPort.write(direction)
    except:
        print("Oops!", error[0])

def displayFrame(title,frame):
    #Display the resulting frames
    cv2.imshow(title, frame)
    key = cv2.waitKey(1)

def checkQrCode(current,path,file):
    if current == file:
        return False
    checkPath = path + file
    return os.path.isfile(checkPath)

def checkRoom(currentQr):
    # Capture the frames
    _, qrFrame = cap.read()
    decodedObjects = pyzbar.decode(qrFrame)
    for obj in decodedObjects:
        #print("Data", obj.data)
        # Slice string to remove first 2 characters and last charecter
        strObj = str(obj.data)[2 : -1 : ]
        strObj = strObj + '.mp3'
        print(strObj)
        if checkQrCode(currentQr,audioPath,strObj) != False:
            currentQr = strObj
            cv2.putText(qrFrame, strObj, (50, 50), font, 1,(255, 0, 0), 3)
            UART(b'0')
            playsound(audioPath + strObj)
        else:
            cv2.putText(qrFrame, "TANIMSIZ QR", (50, 50), font, 1,(255, 0, 0), 3)
            UART(b'3')
    displayFrame("QR FRAME",qrFrame)
    return currentQr
    
def findContours():
    # Capture the frame
    ret, frame = video_capture.read()
    # Crop the image to the bottom half of the initial frame
    croped = frame[60:120, 0:160]
	# Convert to grayscale
    gray = cv2.cvtColor(croped, cv2.COLOR_BGR2GRAY)
    # Gaussian blur
    blur = cv2.GaussianBlur(gray,(5,5),0)
	# Color thresholding
    ret,thresh1 = cv2.threshold(blur,60,255,cv2.THRESH_BINARY_INV)
    # Erode and dilate to remove accidental line detections
    mask = cv2.erode(thresh1, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    # Find the contours of the frame
    contours,hierarchy = cv2.findContours(mask.copy(), 1, cv2.CHAIN_APPROX_NONE)
    return contours,hierarchy,croped

def findOptimalCountour(contours,hierarchy,croped_capture):
    cx = 0
    cy = 0
    if len(contours) > 0:
        c = max(contours, key=cv2.contourArea)
        M = cv2.moments(c)
        cx = int(M['m10']/M['m00'])
        cy = int(M['m01']/M['m00'])
        cv2.line(croped_capture,(cx,0),(cx,720),(255,0,0),1)
        cv2.line(croped_capture,(0,cy),(1280,cy),(255,0,0),1)
        cv2.drawContours(croped_capture, contours, -1, (0,255,0), 1)
    else:
        print ("I don't see the line")
        cv2.putText(croped_capture, "I don't see the line", (50, 50), font, 1,(255, 0, 0), 3) 
    return cx,cy

def calculatePWM(cx,cy,croped_capture):
    if cx >= 120:
        print ("Turn Right!")
        cv2.putText(croped_capture, "SAGA DON", (50, 50), font, 1,(255, 0, 0), 3)
        UART(b'2')
    elif cx < 120 and cx > 50:
        print ("Go Straight!")
        cv2.putText(croped_capture, "DUZ GIT", (50, 50), font, 1,(255, 0, 0), 3)
        UART(b'3')
    elif cx <= 50:
        print ("Turn Left") 
        cv2.putText(croped_capture, "SOLA DON", (50, 50), font, 1,(255, 0, 0), 3)
        UART(b'1')

def run():
    PORT = serial_ports()
    UART(b'0')
    currentQr = "your inro .mp3"
    playsound(audioPath + currentQr)
    while True: 
        try:
            currentQr = checkRoom(currentQr)
            contours,hierarchy,crop_vid = findContours()
            centerX,centerY = findOptimalCountour(contours,hierarchy,crop_vid)
            calculatePWM(centerX,centerY,crop_vid)
            displayFrame("LINE FOLLOWING",crop_vid)
        except:
            print("Oops!", error[1])
            break
run()