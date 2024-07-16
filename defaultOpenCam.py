import cv2
print(cv2.__version__)
dispW=960
dispH=720
flip=2

cam=cv2.VideoCapture(0)
outVid=cv2.VideoWriter('videos/myCam.avi',cv2.VideoWriter_fourcc(*'XVID'))


cam.set(cv2.CAP_PROP_FRAME_WIDTH,dispW)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT,dispH)
while True:
    ret, frame = cam.read()
    cv2.imshow('nanoCam',frame)
    cv2.moveWindow('nanoCam',700,0)
    gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)

    frameSmall=cv2.resize(frame,(320,240))
    graySmall=cv2.resize(gray,(320,240))
    cv2.moveWindow('BW',0,265)
    cv2.moveWindow('nanoSmall',0,0)
    cv2.imshow('BW',graySmall)
    cv2.imshow('nanoSmall',frameSmall)

    if cv2.waitKey(1)==ord('q'):
        break
cam.release()
cv2.destroyAllWindows()