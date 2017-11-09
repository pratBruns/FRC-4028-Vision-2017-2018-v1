'''
Created on Aug 10, 2017

@author: Prat Bruns
'''
#====================================================================================
#Revisions Box
'''
  | Person       | Date       | Reason                       | Successful?    | Notes   
  | PRAT         | 10/7       | Expand the correct contours  |  YYEEEESSSSS   | Ran into a few issues - Had to factor width into filtering
  |              |            | parameters to sort through   |                | Contour does not have to be entirely in screen for it to 
  |              |            | the top 3 (by area) contours |                | select, but it doesn't have to be the biggest thing in screen
  |              |            | and compare (allows for a    |                |
  |              |            | larger target to be in view  |                |
  |              |            | but not select it)           |                |
  |              |            |                              |                |
  | PRAT         | 11/8       | Restructuring the code to    |      Meh       | The targeting system is a little messed up, but it still sees the target
  |              |            | be more intuitive and forces |                | Possible sources of the error:
  |              |            | the code to choose only one  |                |    1) I transfered some value wrong (Looking into constants)
  |              |            | object as the target         |                |    2) Calculation of Center of Target Point is wrong (Top, Left corner of frame is (0,0)
  |              |            |                              |                |    3) Not seeing the correct targets and picking different targets (look into HtoW ratio)
  |              |            |                              |                | Will look into issue further
  |              |            |                              |                |
  |              |            |                              |                |
  |              |            |                              |                |
  |              |            |                              |                |
  |              |            |                              |                |
  |              |            |                              |                |
  |              |            |                              |                |
  |              |            |                              |                |
  |              |            |                              |                |
  |              |            |                              |                |
  |              |            |                              |                |
  |              |            |                              |                |
  |              |            |                              |                |
  |              |            |                              |                |
'''
#====================================================================================
# This example will open a multiple windows and display sequential frames that represent the various manipulations to the image
# it also can identify the blue blocks on a sheet of paper and draw boundaries around them. 

import cv2
import socketserver
import numpy as np
import time
from tracemalloc import Frame
from numpy.ma.bench import xs

#====================================================================================
#set min and max ratios for height and width
ratioMaxH = 2.00
ratioMinH = 1.00
ratioMaxW = 2.00
ratioMinW = 0.95

#====================================================================================
# Define Range Constants of Green Color in HSV
LOWERGREEN = np.array([50,100,100])
UPPERGREEN = np.array([70,255,250])

#====================================================================================
#Define Sources for Cameras
cap = cv2.VideoCapture(0)
#cap2 = cv2.VideoCapture(3)
    
#====================================================================================
#Gather information about the frame 
_,frame1 = cap.read()
frameHeight = frame1.shape[0] 
frameWidth = frame1.shape[1]
frameCenter_X = int(frameWidth/2)
frameCenter_Y = int(frameHeight/2)

#====================================================================================
#Set Up FPS Counter
t0 = time.time()    #define variables 
t1 = time.time()

fpsCount = 1
fpsSum = 0
framesPerSec = str(0)

#====================================================================================
#Set Up Socket Server
'''
class MyTCPHandler(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        print ("{} wrote:".format(self.client_address[0]))
        print (self.data)
        # just send back the same data, but upper-cased
        self.request.sendall(self.data.upper())
        
if __name__ == "__main__":
    HOST, PORT = "localhost", 6060

    # Create the server, binding to localhost on port 6060
    server = socketserver.TCPServer((HOST, PORT), MyTCPHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
'''
#====================================================================================
while(1):       # This is a simple continuous loop that recursively grabs frames from the system default camera.
    #====================================================================================
    t0 = time.time()    # Get starting time of loop
    #====================================================================================
    
    _, frame1 = cap.read()   # Read a BGR frame1 from the camera and store in "frame1"
    #_, frame2 = cap2.read()
    hsv = cv2.cvtColor(frame1, cv2.COLOR_BGR2HSV)    # Convert BGR frame1 to HSV format so that you can more easily filter on a color
    
    # Threshold the HSV image to get only blue colors, based on lower_blue, upper_blue
    mask = cv2.inRange(hsv, LOWERGREEN, UPPERGREEN)
    
    # Bitwise-AND mask and original image and the blue mask to get a final result that "only" has the blue colors.
    res = cv2.bitwise_and(frame1,frame1, mask= mask)
    
    maskcopy = mask  #make a copy of mask, some documents suggest that the contours function changes the image that is passed.
    image, contours, hierarchy = cv2.findContours(maskcopy,cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)     # Find the contours
    cv2.drawContours(frame1, contours, -1, (255,0,0), 2)
    #cv2.drawContours(frame2, contours, -1, (255,0,0), 2)
    
    #Draw Cross Hairs At Center of Frame
    frame1 = cv2.circle(frame1, (frameCenter_X, frameCenter_Y), 10, (255,0,0), 1)  #  Draw a circle using center and radius of target
    frame1 = cv2.line(frame1, (frameCenter_X-10, frameCenter_Y),(frameCenter_X+10, frameCenter_Y), (225,0,0), 1)     # Draw a red horizontal line
    frame1 = cv2.line(frame1, (frameCenter_X, frameCenter_Y-10), (frameCenter_X, frameCenter_Y+10), (225,0,0), 1) 
    
    #====================================================================================
    #Manage Defining Objects
    obj1Exists = False
    obj2Exists = False
    obj3Exists = False    
    
    if len(contours) > 1:
        Obj1 = max(contours, key=cv2.contourArea)
        obj1Exists = True
 
        #=====================================================================================
        #Find the nth largest contour
        goal_ycrcb_mint = np.array([0, 90, 100],np.uint8)
        goal_ycrcb_maxt = np.array([25, 255, 255],np.uint8)
        goal_ycrcb = cv2.inRange(frame1, goal_ycrcb_mint, goal_ycrcb_maxt)
        areaArray = []
        count = 1

        for i, c in enumerate(contours):
            area = cv2.contourArea(c)
            areaArray.append(area)

        #first sort the array by area
        sorteddata = sorted(zip(areaArray, contours), key=lambda x: x[0], reverse=True)

        #find the nth largest contour [n-1][1], in this case 2, 3
        Obj2 = sorteddata[1][1]
        obj2Exists = True
        
        if len(contours) > 2:
            Obj3 = sorteddata[2][1]     
            obj3Exists = True
            
    #======================================================================================
    #Gather Values for Objects
    if (obj1Exists):
        (xf, yf, wf, hf) = cv2.boundingRect(Obj1) 
        obj1Height = hf
        obj1Width = wf
    else:
        obj1Height = 0
        obj1Height = 0 
        
    if (obj2Exists):
        (xs, ys, ws, hs) = cv2.boundingRect(Obj2)
        obj2Height = hs
        obj2Width = ws
    else:
        obj2Height = 0
        obj2Height = 0
        
    if (obj3Exists):
        (xt, yt, wt, ht) = cv2.boundingRect(Obj3)        
        obj3Height = ht
        obj3Width = wt
    else:
        obj3Height = 0
        obj3Width = 0
    
    #===============================================================================
    #Calculate the Ratios
    if (obj1Exists and obj2Exists):
        HeightRatio1to2 = (hf)/hs
        WidthRatio1to2 = (wf)/ws
    else:
        HeightRatio1to2 = 0
        WidthRatio1to2 = 0
            
    if(obj2Exists and obj3Exists):
        HeightRatio2to3 = (hs)/ht
        WidthRatio2to3 = (ws)/wt
    else:
        HeightRatio2to3 = 0
        WidthRatio2to3 = 0
            
    if(obj1Exists and obj3Exists):
        HeightRatio1to3 = (hf)/ht
        WidthRatio1to3 = (wf)/wt
    else:
        HeightRatio1to3 = 0
        WidthRatio1to3 = 0
        
    #===============================================================================
    #Check if Ratios are within Limits
    is1to2WISpec = False
    is2to3WISpec = False
    is1to3WISpec = False
    
    if (ratioMinH <= HeightRatio1to2 <= ratioMaxH and ratioMinW <= WidthRatio1to2 <= ratioMaxW):
        is1to2WISpec = True
    
    if (ratioMinH <= HeightRatio2to3 <= ratioMaxH and ratioMinW <= WidthRatio2to3 <= ratioMaxW):
        is2to3WISpec = True 
        
    if (ratioMinH <= HeightRatio1to3 <= ratioMaxH and ratioMinW <= WidthRatio1to3 <= ratioMaxW):
        is1to3WISpec = True
    
    #================================================================================
    #Make Decision on which Object to Use as Goal
    targetExists = False
    
    if(is1to2WISpec):
        targetCornerPoint_X = xf #The point (x,y) given by the boundingRect OpenCV Function is the Top-Left (NW) corner
        targetCornerPoint_Y = yf
        targetHeight = hf
        targetWidth = wf
    
        targetExists = True
        
    elif(is2to3WISpec):
        targetCornerPoint_X = xs #The point (x,y) given by the boundingRect OpenCV Function is the Top-Left (NW) corner
        targetCornerPoint_Y = ys
        targetHeight = hs
        targetWidth = ws
        
        targetExists = True
        
    elif(is1to3WISpec):
        targetCornerPoint_X = xf #The point (x,y) given by the boundingRect OpenCV Function is the Top-Left (NW) corner
        targetCornerPoint_Y = yf
        targetHeight = hf
        targetWidth = wf
        
        targetExists = True
        
    #==================================================================================
    #Deal with Target if it Exists
    if targetExists:
        
        #Calculate Data to send to RoboRio
    
        centerOfTarget_X = int(targetCornerPoint_X + (targetHeight/2))
        centerOfTarget_Y = int(targetCornerPoint_Y + (targetWidth/2))
    
        SW_X = targetCornerPoint_X
        SW_Y = targetCornerPoint_Y - targetHeight
        SE_X = targetCornerPoint_X + targetWidth
        SE_Y = targetCornerPoint_Y - targetHeight
    
        #==================================================================================
        #Draw Target and Line of Travel
    
        frame1 = cv2.circle(frame1,(centerOfTarget_X, centerOfTarget_Y),10, (0,0,255), 1)  #  Draw a circle using center and radius of target
        frame1 = cv2.line(frame1,(centerOfTarget_X-10, centerOfTarget_Y),(centerOfTarget_X+10, centerOfTarget_Y),(0,0,255),1)     # Draw a red horizontal line
        frame1 = cv2.line(frame1,(centerOfTarget_X, centerOfTarget_Y-10),(centerOfTarget_X, centerOfTarget_Y+10),(0,0,255),1)     # Draw a red horizontal line
            
        #Calculate offset from center of frame1 to center of target
        targetOffset_X = centerOfTarget_X - frameCenter_X
        targetOffset_Y = frameCenter_Y - centerOfTarget_Y
    
        #Draw Line of Where the Robot must move
        frame1 = cv2.line(frame1,(centerOfTarget_X,centerOfTarget_Y),(frameCenter_X,frameCenter_Y),(225,225,225),2)
            
        #Write Distance to Target Point Coordinates to the Screen
        centerPoint = "(" + str(targetOffset_X) + "," + str(targetOffset_Y) + ")"
        cv2.putText(frame1, centerPoint, (475,400), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2, cv2.LINE_AA)
                    
    #====================================================================================
    t1 = time.time()    # Get ending time for FPS  loop 
    
    #====================================================================================
    #Manage FPS averaging 
    fpsSum = fpsSum + (t1-t0)
    if (fpsCount == 10 ):
        framesPerSec = "FPS:"+str(int(1/(fpsSum/10)))   #Calculate frames per sec., and convert to a string
        fpsCount = 0 # reset counter
        fpsSum = 0  #reset sum
    cv2.putText(frame1,framesPerSec,(500,450), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2, cv2.LINE_AA)  # write FPS to the processed frame1
    fpsCount = fpsCount+1 #increment  counter
    
    #====================================================================================    
    cv2.imshow('Camera-frame1 with contour',frame1)
    #cv2.imshow('Camera Raw', frame2)
         
    # exit while loop using escape key
    k = cv2.waitKey(1) & 0xFF
    if k == 27:
        break

cv2.destroyAllWindows()     # Best practice is to clean up all windows before exiting.

#====================================================================================
#Preserves Last Frame Until ESC key pressed again
cv2.imshow('Final Frame with contours',frame1)
#cv2.imshow('Camera Raw', frame2)
#cv2.imshow('resize of Frame with contours',res)
k = cv2.waitKey(0) & 0xFF
if k == 27:
    cv2.destroyAllWindows()     # clean up after ESC key. Best practice is to clean up all windows before exiting.