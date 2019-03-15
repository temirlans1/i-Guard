# -*- coding: utf-8 -*-
import yaml
import numpy as np
import cv2
import time
import pickle
import json
import psycopg2
import requests
import telegram
import threading
from dbconfig import dbconfig



last_time_sent = time.time()

with open('config.json') as f:
    config = json.load(f)

fn = config["video_source"]
fn_yaml = config["points_source"]
fn_out = r"../datasets/output.mp4"

bot = telegram.Bot(token=config["bot_token"])


def cross_product(A, B):
	return A[0]*B[1] - A[1]*B[0]

def intersect(A, B):
    (o1,p1) = A
    (o2,p2) = B
    d1 = (p1[0]-o1[0], p1[1]-o1[1])
    d2 = (p2[0]-o2[0], p2[1]-o2[1])
    
    cross = cross_product(d1,d2)

    x = (o2[0]-o1[0], o2[1]-o1[1])

    if abs(cross) == 0:
        return False

    t = cross_product(x,d2)
    u = cross_product(x,d1)

    t = float(t)/cross
    u = float(u)/cross

    if 0<t<1 and 0<u<1:
        inter1 = (o1[0]+p1[0]*u,o1[1]+p1[1]*u)
        inter2 = (o2[0]+p2[0]*t, o2[1]+p2[1]*t)
        return True

    return False

def sendMessage(image_path):
    # url = "https://api.telegram.org/bot/sendMessage"
    # params = {"chat_id": ,
    #         "text": "Alert",
    #         "photo": frame
    #         }

    # response = requests.get(url, params = params)
    bot.send_message(chat_id=config["telegram_chat_id"], text=config["alert_message"])
    bot.send_photo(chat_id=config["telegram_chat_id"], photo=open(image_path, 'rb'))

def sendAlert(frame):
    global last_time_sent
    last_time_sent = time.time()
    print("Alert")
    imname = "/frame" + str(int(last_time_sent)) + ".jpg"
    im_path = config["violation_frame_path"] + imname
    cv2.imwrite(im_path, frame)
    sql = """INSERT INTO fence_violations(violation_id ,frame_name, violation_time)
    VALUES({},'{}', {});""".format(int(last_time_sent), imname, int(last_time_sent))
    
    try:
        params = dbconfig()
        conn = psycopg2.connect(**params) # may need password
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(sql)
        cur.close()
        send_thread = threading.Thread(target=sendMessage, args=(im_path,))
        send_thread.start()
    finally:
        conn.close()
    


# Set capture device or file
cap = cv2.VideoCapture(fn)
if not config["is_stream"]:
    video_info = {'fps':    cap.get(cv2.CAP_PROP_FPS),
                'width':  int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'fourcc': cap.get(cv2.CAP_PROP_FOURCC),
                'num_of_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT))}
    cap.set(cv2.CAP_PROP_POS_FRAMES, config['start_frame']) # jump to frame

# Define the codec and create VideoWriter object
if config['save_video']:
    fourcc = cv2.VideoWriter_fourcc(*'MP4V') # options: ('P','I','M','1'), ('D','I','V','X'), ('M','J','P','G'), ('X','V','I','D')
    out = cv2.VideoWriter(fn_out, fourcc, 25.0, #video_info['fps'], 
                          (2000, 1000))


# Create Background subtractor
if config['motion_detection']:
    fgbg = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold= config['motion_treshold'], detectShadows=False)
    #fgbg = cv2.createBackgroundSubtractorKNN(history=100, dist2Threshold=800.0, detectShadows=False)

# Read YAML data (parking space polygons)
lines = []
with open(fn_yaml, 'r') as stream:
    line_data = yaml.load(stream)
for line in line_data:
    lines.append(tuple(line['points']))
    
lines = np.array(lines)
    



kernel_erode = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3)) # morphological kernel
#kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(13,13)) # morphological kernel
kernel_dilate = cv2.getStructuringElement(cv2.MORPH_RECT,(5,19))
frame_num = 0
print("Video analysis started")
last_clear_time = time.time()
while(cap.isOpened()):
    video_cur_frame = cap.get(cv2.CAP_PROP_POS_FRAMES) # Index of the frame to be decoded/captured next
    
    ret, frame = cap.read()
    if ret == False:
        print("Capture Error")
        break
    
    frame_blur = cv2.GaussianBlur(frame.copy(), (5,5), 3)
    frame_gray = cv2.cvtColor(frame_blur, cv2.COLOR_BGR2GRAY)
    frame_out = frame.copy()
    laplacian = cv2.Laplacian(frame_gray, cv2.CV_64F)
    #cv2.imshow("Laplace", laplacian)
    for line in lines:
        li_x, li_y = (line[0][0], line[0][1]), (line[1][0], line[1][1])
        cv2.line(frame_out, li_x, li_y, (255,0,0), 2)
    
    if config['motion_detection']:
        fgmask = fgbg.apply(frame_blur)
        bw = np.uint8(fgmask==255)*255    
        bw = cv2.erode(bw, kernel_erode, iterations=1)
        bw = cv2.dilate(bw, kernel_dilate, iterations=1)
        #cv2.imshow("BW", bw)
        (_, cnts, _) = cv2.findContours(bw.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # loop over the contours

        for c in cnts:
            # if the contour is too small, ignore it
            if cv2.contourArea(c) < config['min_area_motion_contour']:
                continue
            (x, y, w, h) = cv2.boundingRect(c)
            amt = 0
            cv2.rectangle(frame_out, (x, y), (x + w, y + h), (255, 0, 0), 2)
          
            for line in lines:
                li_x, li_y = (line[0][0], line[0][1]), (line[1][0], line[1][1])
                diagonal1 = ((x, y), (x + w, y + h))
                diagonal2 = ((x + w, y), (x, y + h))
                test_line = (li_x, li_y)
                p1 = intersect(test_line, diagonal1)
                p2 = intersect(test_line, diagonal2)
                if(p1 or p2):
                    amt += 1
                    cv2.line(frame_out, li_x, li_y, (0,255,0), 2)
                    
            if amt == len(lines):
                if abs(time.time() - last_clear_time) >= float(config["violation_seconds_to_wait"]) and abs(time.time() - last_time_sent) > float(config['alert_delay']):
                    sendAlert(frame)
            else:
                last_clear_time = time.time()
            
    # write the output frame
    # small_frame = cv2.resize(frame_out, (0,0), fx=0.5, fy=0.5) 
    if config['save_video']:
        out.write(frame_out)  
    
    # Display video
    frame_out = cv2.resize(frame_out, (0,0), fx=0.5, fy=0.5) 
    cv2.imshow('frame', frame_out)
    #cv2.imshow('background mask', bw)
    k = cv2.waitKey(1)
    if k == ord('q'):
        break

cap.release()
if config['save_video']: out.release()
cv2.destroyAllWindows()
