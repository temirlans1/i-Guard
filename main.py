import yaml
import numpy as np
import cv2
import time
import pickle
import json
import psycopg2
import threading
# import telegram
import multiprocessing
import queue as queuelib
from dbconfig import dbconfig
import os
with open('config.json') as f:
    config = json.load(f)

# bot = telegram.Bot(token=config["bot_token"])

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

def sendMessage(image_path, cam_id):
    pass
    # url = "https://api.telegram.org/bot/sendMessage"
    # params = {"chat_id": ,
    #         "text": "Alert",
    #         "photo": frame
    #         }

    # response = requests.get(url, params = params)
    # duration = 1  # seconds
    # freq = 440  # Hz
    # os.system('play -nq -t alsa synth {} sine {}'.format(duration, freq))
    # bot.send_message(chat_id=config["telegram_chat_id"][cam_id], text=config["alert_message"])
    # bot.send_photo(chat_id=config["telegram_chat_id"][cam_id], photo=open(image_path, 'rb'))

def sendAlert(frame, cam_id):
    last_time_sent = time.time()
    print("Alert")
    imname = "/frame" + str(int(last_time_sent)) + ".jpg"
    im_path = config["violation_frame_path"] + imname
    cv2.imwrite(im_path, frame)
    
    sql = """INSERT INTO fence_violations(violation_id ,frame_name, violation_time)
    VALUES({},'{}', {});""".format((last_time_sent % 1000000) *len(config["video_sources"]) + cam_id, imname, int(last_time_sent))
    try:
        params = dbconfig()
        conn = psycopg2.connect(**params) # may need password
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(sql)
        cur.close()
        send_thread = threading.Thread(target=sendMessage, args=(im_path, cam_id))
        send_thread.start()
    finally:
        conn.close()
    return last_time_sent

kernel_erode = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3)) # morphological kernel
#kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(13,13)) # morphological kernel
kernel_dilate = cv2.getStructuringElement(cv2.MORPH_RECT,(5,19))

# Create Background subtractor
if config['motion_detection']:
    fgbg = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold= config['motion_treshold'], detectShadows=False)
    #fgbg = cv2.createBackgroundSubtractorKNN(history=100, dist2Threshold=800.0, detectShadows=False)

# Read YAML data (parking space polygons)

def captureCam(cam_id):
    fn = config["video_sources"][cam_id]
    fn_yaml = config["points_sources"][cam_id]
    # Set capture device or file
    cap = cv2.VideoCapture(fn)

    queue = queuelib.Queue()
    last_time_sent = time.time()

    min_x = 10000
    min_y = 10000
    max_x = 0
    max_y = 0

    lines = []
    with open(fn_yaml, 'r') as stream:
        line_data = yaml.load(stream)
    for line in line_data:
        lines.append(tuple(line['points']))
        min_x = min(min_x, line['points'][0][0], line['points'][1][0])
        min_y = min(min_y, line['points'][0][1], line['points'][1][1])
        max_x = max(max_y, line['points'][0][0], line['points'][1][0])
        max_y = max(max_y, line['points'][0][1], line['points'][1][1])
        
    lines = np.array(lines)

    for line in lines:
        line[0][0] -= min_x - 50
        line[1][0] -= min_x - 50
        line[0][1] -= min_y - 50
        line[1][1] -= min_y - 50
 

    print("Video analysis started")
    last_clear_time = time.time()
    alert_amt = 0
    frame_amt = config["frame_num_thresh"]
    for i in range(0, frame_amt):
        queue.put(0)
    frame_num = 0
    while(cap.isOpened()):
        frame_num += 1
        if(frame_num % 50 == 0):
            print(frame_num)
        ret, frame = cap.read()
        if ret == False:
            print("Capture Error")
            break
        
        
        
        frame = frame[min_y - 50: max_y + 50, min_x - 50:max_x + 50]
        frame_blur = cv2.GaussianBlur(frame.copy(), (5,5), 3)
        frame_out = frame.copy()
        
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
            is_alert = False
            for c in cnts:
                # if the contour is too small, ignore it
                if cv2.contourArea(c) < config['min_area_motion_contour']:
                    continue
                (x, y, w, h) = cv2.boundingRect(c)
                amt = 0
                #cv2.rectangle(frame_out, (x, y), (x + w, y + h), (255, 0, 0), 2)
            
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
                    is_alert = True
                    alert_amt += 1
                    print(alert_amt, frame_amt)
                    if (alert_amt / frame_amt >= config["alert_ratio"]) and (abs(time.time() - last_time_sent) >= float(config['alert_delay'])):
                        last_time_sent = sendAlert(frame, cam_id)
            queue.put(is_alert)
            alert_amt -= int(queue.get())
        # write the output frame
        # small_frame = cv2.resize(frame_out, (0,0), fx=0.5, fy=0.5) 
        
        # Display video
        #frame_out = cv2.resize(frame_out, (0,0), fx=0.5, fy=0.5) 
        cv2.imshow('frame {}'.format(cam_id), frame_out)
        #cv2.imshow('background mask', bw)
        k = cv2.waitKey(1)
        if k == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if(len(config["video_sources"]) != len(config["points_sources"])):
    print("Number of streams not equal to number of yml files")

if __name__ == '__main__':
    jobs = []
    for i in range(len(config["video_sources"])):
        process = multiprocessing.Process(target=captureCam, args=(i,))
        jobs.append(process)

    for j in jobs:
        j.start()

    for j in jobs:
        j.join()
