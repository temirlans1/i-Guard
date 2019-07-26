import tkinter as tk
from tkinter import messagebox
import cv2
import PIL.Image, PIL.ImageTk
import time 
from VideoCap import MyVideoCapture
from ScrollFrame import ScrollFrame
import json
import threading
import numpy as np
import os
from database import Database
from Notifications import Notifications
from SettingWindow import SettingWindow
from HumanDetection import DetectorAPI
import multiprocessing
#print(cv2.getBuildInformation())
#print(cv2.cuda.getCudaEnabledDeviceCount)

class App:

    def __init__(self, window, window_title):
        self.window = window
        self.window.geometry("1230x700")
        self.window.title(window_title)
        #self.video_sources = video_sources
        self.panedwindow = tk.PanedWindow(window, orient = tk.HORIZONTAL, sashwidth = 5, sashrelief = tk.RAISED)
        self.panedwindow.pack(fill = tk.BOTH, expand = True)

        
        #self.vid_frame = tk.Frame(self.panedwindow, width = 400,  height = 300, relief = tk.FLAT)
        
        #self.alert_frame = tk.Frame(self.panedwindow, width = 300,  height = 300, relief = tk.FLAT, bg = 'gray')
        
        self.vid_frame = ScrollFrame(self.panedwindow, width = 1000, height = 500, relief = tk.FLAT)
        self.alert_frame = ScrollFrame(self.panedwindow, width = 50,  height = 500, relief = tk.FLAT)


        self.load_alerts()
        self.load_video()
        
        self.proc_queue = []

        self.panedwindow.add(self.vid_frame, width = 1025)
        self.panedwindow.add(self.alert_frame, width = 50)
        # Button that lets the user take a snapshot
        # After it is called once, the update method will be automatically called every delay milliseconds
        self.delay = 1
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.exit_time = False

        self.check_alert()
        self.update()
        
        
        self.window.mainloop()

    def load_alerts(self):
        self.db = Database("alert_db.db")
        self.notes = []
        self.alert_label = tk.Label(self.alert_frame.viewPort, text = "Here are the alerts")
        self.alert_label.pack(side = tk.TOP)
        all_data = self.db.select_all()
        self.row_number = len(all_data)
        for i, data in enumerate(all_data):
            note = Notifications(self.alert_frame.viewPort, self.db, from_db = True, db_data = data)
            note.button.pack(expand = 1, side = tk.BOTTOM)
            self.notes.append(note)
        



    def load_video(self):
        with open('config.json') as f:
            self.config = json.load(f)
        
        video_sources = self.config["video_sources"]
        points_sources = self.config["points_sources"]
        self.show_amt = self.config["show_amt"]


        
        self.finished_amt = [0]
        self.start_amt = [0]
        self.videos = []
        self.panel = []
        self.alert_queue = [[]]
        self.settings_button = tk.Button(self.vid_frame.viewPort, text = "Settings", height = 2, relief = tk.FLAT, command = self.createSettings)
        self.settings_button.grid(row = 0, columnspan = 2)
        for i, video_source in enumerate(video_sources):
            self.videos.append(MyVideoCapture(video_source, points_sources[i], i, self.config, self.panel))

        
        for i, vid in enumerate(self.videos):
            if i >= self.show_amt:
                break
            img = PIL.ImageTk.PhotoImage(image = PIL.Image.new('RGB', (500,300), (0, 0, 0)))
            self.panel.append(tk.Label(self.vid_frame.viewPort, image=img))
            self.panel[i].grid(row = (i // 2) + 1, column = i % 2)

    def createSettings(self):
        self.settingsWindow = SettingWindow(tk.Toplevel(self.window), self.videos, self.config)
        self.settingsWindow.window.wm_attributes("-topmost", 1)
        self.settingsWindow.window.protocol("WM_DELETE_WINDOW", self.onClosingSettings)

    
    def onClosingSettings(self):
        i = 0
        for panel in self.panel:
            panel.destroy()
        while i < len(self.config["video_sources"]):
            if(self.config["video_sources"][i] == None):
                try:
                    del self.config["video_sources"][i]
                    del self.config["points_sources"][i]
                    i -= 1
                except:
                    pass
            i += 1
        with open('config.json', 'w') as f:
            json.dump(self.config, f, indent = 4)
        self.settingsWindow.window.destroy()
        self.reload_vid()

    def reload_vid(self):
        self.exit_time = True
        time.sleep(1)
        self.load_video()
        self.exit_time = False
        #self.update()
        


    def check_alert(self):
        data_rows = self.db.select_with_offset(self.row_number)
        
        for row in data_rows:
            self.row_number += 1
            note = Notifications(self.alert_frame.viewPort, self.db, from_db = True, db_data = row)
            note.button.pack(expand = 1, side = tk.BOTTOM)
            self.notes.append(note)       
        
        self.window.after(1000, self.check_alert)

    def update(self):
        n = len(self.videos)
        if self.exit_time:
            self.paused = True
        else:
            self.paused = False
            self.finished_amt = [0]
            self.start_amt = [0]
            for i in range(n):
                dont_show = False
                if i >= self.show_amt:
                    dont_show = True

                #process = threading.Thread(target=self.videos[i].get_frame, args=(self.finished_amt, dont_show))
                #self.proc_queue.append(process)
                #process.start()
                #self.start_amt[0] += 1
                if self.videos[i] != None:
                    #self.start_amt[0] += 1
                    self.videos[i].showFrame( dont_show)
            
            self.window.after(self.delay, self.update) 
        #self.window.after(10, self.check_thread)
        
    # def check_thread(self):
    #     if self.finished_amt[0] < self.start_amt[0]:
    #         self.window.after(10, self.check_thread)
    #     elif self.exit_time:
    #         self.paused = True
    #     else:
    #         self.window.after(self.delay, self.update) 

    def on_closing(self):
        self.exit_time = True
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            time.sleep(0.2)
            self.window.destroy()
        else:
            self.exit_time = False
            self.update()
    
# class MyVideoCapture:
#     def __init__(self, video_source=0):
#         # Open the video source
#         self.vid = cv2.VideoCapture(video_source)
#         if not self.vid.isOpened():
#             raise ValueError("Unable to open video source", video_source)

#         # Get video source width and height
#         self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
#         self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

#     def get_frame(self):
#         if self.vid.isOpened():
#             ret, frame = self.vid.read()
#             if ret:
#                 # Return a boolean success flag and the current frame converted to BGR
#                 return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
#             else:
#                 return (ret, None)
#         else:
#             return (ret, None)

#     # Release the video source when the object is destroyed
#     def __del__(self):
#         if self.vid.isOpened():
#             self.vid.release()
 
# Create a window and pass it to the Application object

# Set environtment key
os.environ["SENDGRID_API_KEY"] = "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"

def start_app():
    App(tk.Tk(), "Tkinter and OpenCV")

#Open App
from newMain import analyze



analyze_thread = multiprocessing.Process(target=analyze)
desktop_thread = multiprocessing.Process(target=start_app)


desktop_thread.start()
analyze_thread.start()

desktop_thread.join()




analyze_thread.terminate()
# import requests
# import cv2
# print(cv2.getBuildInformation())
# # response = requests.get("https://api.telegram.org/bot748225256:AAFFhmHUnWHXnj8J4-gnbeLZNJXLw2F3jak/getUpdates")
# # print(response.content)
