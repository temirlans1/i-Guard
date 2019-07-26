import cv2
import time 
import yaml
import numpy as np
import cv2
import time
import threading
import json
import tkinter
import PIL.Image, PIL.ImageTk
import telegram
import queue as queuelib
from database import Database
#from sendMail import sendMail
import os


def sendMessage(image_path, timesec, cam_id, config):
    #sendMail(image_path, timesec, config["to_mail"])
    bot = telegram.Bot(token=config["bot_token"])
    #duration = 1  # seconds
    #freq = 440  # Hz
    #os.system('play -nq -t alsa synth {} sine {}'.format(duration, freq))
    bot.send_message(chat_id=config["telegram_chat_id"], text=config["alert_message"])
    bot.send_photo(chat_id=config["telegram_chat_id"], photo=open(image_path, 'rb'))

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

class MyVideoCapture:


    def sendAlert(self, frame):
        
        frame = frame[0]
        self.last_time_sent = time.time()
        print("Alert")

        imname = "/{}frame".format(self.cam_id) + str(int(self.last_time_sent)) + ".jpg"
        im_path = self.config["violation_frame_path"] + imname
        cv2.imwrite(im_path, frame)
        abspath = os.path.abspath(im_path)
        database = Database("alert_db.db")
        database.insert(abspath)

        try:
            send_thread = threading.Thread(target= sendMessage, args=(im_path, self.last_time_sent, self.cam_id, self.config))
            send_thread.start()
        except:
            pass
            
    def __init__(self, video_source, point_source, cam_id, config, odapi):
        
        self.odapi = odapi
        self.second_frame = False
        self.cam_id = cam_id
        self.config = config
        self.video_source = video_source
        self.point_source = point_source
        self.human_threshold = config["human_threshold"]
        self.is_night = False
        # Open the video source
        self.kernel_erode = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3)) # morphological kernel
        #kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(13,13)) # morphological kernel
        self.kernel_dilate = cv2.getStructuringElement(cv2.MORPH_RECT,(5,19))
        #self.new_kernel = np.ones((5, 5), np.uint8)
        # Create Background subtractor
        self.fgbg = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold= self.config['motion_treshold'], detectShadows=False)
        #self.fgbg = cv2.createBackgroundSubtractorKNN(history=300, dist2Threshold=800.0, detectShadows=False)
        #self.fgbg = cv2.bgsegm.createBackgroundSubtractorMOG()
        
        #self.fgbg = cv2.createBackgroundSubtractorKNN(dist2Threshold=1600.0, detectShadows = False)
        fn = video_source
        fn_yaml = point_source

        self.cap = cv2.VideoCapture(fn)
        """(major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')
        if int(major_ver)  < 3 :
            fps = self.cap.get(cv2.cv.CV_CAP_PROP_FPS)
            print ("Frames per second using video.get(cv2.cv.CV_CAP_PROP_FPS): {0}".format(fps))
        else :
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            print ("Frames per second using video.get(cv2.CAP_PROP_FPS) : {0}".format(fps))
        """
        self.queue = queuelib.Queue()
        self.last_time_sent = time.time()
        full_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        full_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

        min_x = 10000
        min_y = 10000
        max_x = 0
        max_y = 0

        lines = []
        try:
            with open(fn_yaml, 'r') as stream:
                line_data = yaml.load(stream)
            
            for idx in line_data:
                line = line_data[idx]
                lines.append(line_data[idx])
                min_x = min(min_x, line[0], line[2])
                min_y = min(min_y, line[1], line[3])
                max_x = max(max_x, line[0], line[2])
                max_y = max(max_y, line[1], line[3])

            if(min_x < 0 or max_x > full_width or min_y < 0 or max_y > full_height):
                lines = []
        except:
            pass

        self.lines = np.array(lines)
        
        self.min_x = int(max(min_x - self.config["frame_width"], 0))
        self.min_y = int(max(min_y - self.config["frame_width"], 0))
        self.max_x = int(min(max_x + self.config["frame_width"], full_width))
        self.max_y = int(min(max_y + self.config["frame_width"], full_height))

        if len(self.lines) == 0:
            self.min_x = 0
            self.min_y = 0
            self.max_x = 1
            self.max_y = 1


        for line in self.lines:
            line[0] -= self.min_x
            line[2] -= self.min_x
            line[1] -= self.min_y
            line[3] -= self.min_y
        
        print("Video analysis started cam {}".format(video_source))
        self.last_clear_time = time.time()
        self.alert_amt = 0
        for i in range(0, self.config["frame_num_thresh"]):
            self.queue.put(0)
        
        
    def getOnlyFrame(self):
        ret, frame = self.cap.read()
        if ret == False:
            return None
        for line in self.lines:
            li_x, li_y = (line[0] + self.min_x, line[1] + self.min_y), (line[2] + self.min_x, line[3] + self.min_y)
            cv2.line(frame, li_x, li_y, (255,0,0), 2)
        return frame
        

    def getFrame(self):
        #try:
        ret, frame = self.cap.read()
        
        self.second_frame = not self.second_frame
        
        if(self.second_frame == False):
            ret = False

        
        #frame_out = frame.copy()
        frame_out = frame.copy()
        frame = frame[self.min_y : self.max_y, self.min_x : self.max_x]
        #frame = frame[self.min_y : self.max_y, self.min_x : self.max_x]
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_blur = cv2.GaussianBlur(frame, (5,5), 3)

        for line in self.lines:
            li_x, li_y = (line[0] + self.min_x, line[1] + self.min_y), (line[2] + self.min_x, line[3] + self.min_y)
            cv2.line(frame_out, li_x, li_y, (255,0,0), 2)

        # if not dont_show:
        #     img = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(cv2.cvtColor(cv2.resize(frame_out, (self.config["vid_shape"][0], self.config["vid_shape"][1])), cv2.COLOR_BGR2RGB)))
        #     #canvas[self.cam_id].create_image(0, 0, image = photo[self.cam_id], anchor = tkinter.NW)
        #     self.panel[self.cam_id].configure(image=img)
        #     self.panel[self.cam_id].image = img
        bw = None
        
        if self.config['motion_detection']:
            
            fgmask = self.fgbg.apply(frame_blur)
            #fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, self.new_kernel)
            bw = np.uint8(fgmask==255)*255
            bw = cv2.erode(bw, self.kernel_erode, iterations=1)
            bw = cv2.dilate(bw, self.kernel_dilate, iterations=1)
            #cv2.imshow("BW", bw)
            #print(cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE))
            ( cnts, _) = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            #cv2.rectangle(frame_out, (self.min_x, self.min_y), (self.max_x, self.max_y), (0, 255, 0), 2)
            li1_x, li1_y, li2_x, li2_y = (0,0,0,0)

            for line in self.lines:
                li1_x, li1_y = (line[0] + self.min_x + 150, line[1] + self.min_y), (line[2] + self.min_x + 20, line[3] + self.min_y)
                li2_x, li2_y = (line[0] + self.min_x - 150, line[1] + self.min_y), (line[2] + self.min_x - 20, line[3] + self.min_y)

            left_line = (li1_x, li1_y)
            right_line = (li2_x, li2_y)
            
            #cv2.line(frame_out, li1_x, li1_y, (0,0,255), 2)
            #cv2.line(frame_out, li2_x, li2_y, (0,0,255), 2)
            if len(cnts) > 0:
                self.queue.put(1)
                self.alert_amt += 1
                self.alert_amt -= int(self.queue.get())
                if (self.alert_amt / self.config["frame_num_thresh"] >= self.config["alert_ratio"]):
                    # loop over the contours
                    is_alert = False
                    for c in cnts:
                        # if the contour is too small, ignore it
                        if cv2.contourArea(c) < self.config['min_area_motion_contour']:
                            continue
                        (x, y, w, h) = cv2.boundingRect(c)
                        amt = 0
                        #cv2.rectangle(frame_out, (x + self.min_x, y + self.min_y), (x + self.min_x + w, y + self.min_y + h), (255, 0, 0), 2)

                        diagonal1 = ((x + self.min_x, y + self.min_y), (x + self.min_x + w, y + self.min_y + h))
                        diagonal2 = ((x + self.min_x + w, y + self.min_y), (x + self.min_x, y + self.min_y + h))

                        #cv2.line(frame_out, diagonal1[0], diagonal1[1], (0,0,255), 2)
                        #cv2.line(frame_out, diagonal2[0], diagonal2[1], (0,0,255), 2)
                        
                        left_int1 = intersect(left_line, diagonal1)
                        left_int2 = intersect(left_line, diagonal2)

                        right_int1 = intersect(right_line, diagonal1)
                        right_int2 = intersect(right_line, diagonal2)


                        if(left_int1 or left_int2 or right_int1 or right_int2):
                            print("Motion crossed the line")
                            amt += 1
                            boxes, scores, classes, num = self.odapi.processFrame(frame)

                            # Visualization of the results of a detection.

                            for i in range(len(boxes)):
                                # Class 1 represents human
                                box = boxes[i]
                                if classes[i] == 1 and scores[i] > self.human_threshold:
                                    cv2.rectangle(frame_out,(box[1] + self.min_x, box[0] + self.min_y),(box[3] + self.min_x, box[2] + self.min_y),(0,0,255),2)
                                    print("Human detected")
                                    human_diag1 = (box[1] + self.min_x, box[0] + self.min_y),(box[3] + self.min_x, box[2] + self.min_y)
                                    human_diag2 = (box[3] + self.min_x, box[0] + self.min_y),(box[1] + self.min_x, box[2] + self.min_y)

                                    #cv2.line(frame_out, human_diag1[0], human_diag1[1], (0,0,255), 2)
                                    #cv2.line(frame_out, human_diag2[0], human_diag2[1], (0,0,255), 2)
                                    mainLine_x = 0
                                    mainLine_y = 0
                                    for line in self.lines:
                                        mainLine_x, mainLine_y = (line[0] + self.min_x, line[1] + self.min_y), (line[2] + self.min_x, line[3] + self.min_y)

                                    mainLine = (mainLine_x, mainLine_y)
                                    
                                    human_int1 = intersect(mainLine, human_diag1)
                                    human_int2 = intersect(mainLine, human_diag2)

                                    if(human_int1 or human_int2):
                                        if (abs(time.time() - self.last_time_sent) >= float(self.config['alert_delay'])):
                                            cv2.line(frame_out, mainLine_x, mainLine_y, (0,0,255), 2)
                                            print("Human crossed the line")
                                            print("Alert")
                                            self.sendAlert([frame_out])
                            #cv2.line(frame_out, li_x, li_y, (0,255,0), 2)
            elif len(cnts) == 0:
                self.queue.put(0)
                self.alert_amt -= int(self.queue.get())
        #return frame_out.copy()
        #except:
        #    finished_amt[0] += 1 
    # Release the video source when the object is destroyed
    def __del__(self):
        if self.cap.isOpened():
            self.cap.release()