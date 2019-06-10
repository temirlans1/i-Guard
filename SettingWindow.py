import tkinter as tk
from tkinter import messagebox
from ScrollFrame import ScrollFrame
from LineConfig import PaintApp
from VideoCap import MyVideoCapture
import json
import random
class SettingWindow():
    def __init__(self, window, videos, config):
        self.config = config
        self.window = window
        self.window.geometry("500x500")
        self.main_frame =  ScrollFrame(self.window, relief = tk.FLAT, width = 500, height = 500)
        self.main_frame.pack(fill = tk.BOTH, expand = True)
        #self.main_frame.viewPort.pack(fill = tk.BOTH)
        self.videos = videos
        self.vid_frames = []
        for i, video in enumerate(videos):
            self.addLabel(video.video_source, i)

        
        self.add_frame = tk.Frame(self.main_frame.viewPort, borderwidth = 5)
        self.add_frame.pack(side = tk.BOTTOM, fill = tk.X, pady = 10, expand = False)
        add_label = tk.Label(self.add_frame, text = "Video Path: ")
        self.add_entry = tk.Entry(self.add_frame, width = 40)
        add_button = tk.Button(self.add_frame, text = "Add Video", command = self.addVideo)
        
        add_button.pack(side = tk.RIGHT)
        add_label.pack(side = tk.LEFT)
        self.add_entry.pack(side = tk.LEFT)
    
    def addLabel(self, vid_source, idx):
        vid_frame = tk.Frame(self.main_frame.viewPort, borderwidth = 5)
        vid_frame.pack(side = tk.TOP, fill = tk.X, pady = 10, expand = False)
        vid_label = tk.Label(vid_frame, text = "Video Path : {}".format(vid_source))
        vid_button = tk.Button(vid_frame, text = "Configure Lines", command = lambda idx = idx:self.drawLines( idx))
        del_button = tk.Button(vid_frame, text = "Delete", command = lambda idx = idx:self.deleteVid(idx))
        del_button.pack(side = tk.RIGHT, padx = 10)
        vid_button.pack(side = tk.RIGHT)
        vid_label.pack(side = tk.LEFT)
        self.vid_frames.append(vid_frame)

    def deleteVid(self, idx):
        if messagebox.askokcancel("Delete", "Do you want to delete?", parent = self.window):
            try:
                self.config["video_sources"][idx] = None
                self.config["points_sources"][idx] = None
            except:
                pass


            self.vid_frames[idx].destroy()
            self.videos[idx] = None
            print(len(self.vid_frames))


    def addVideo(self):
        vid_path = self.add_entry.get()
        if len(vid_path) > 0:
            coord_path = "../datasets/coords{}_{}.yml".format(len(self.videos), random.randint(1, 100))


            k = len(self.vid_frames)
            video = MyVideoCapture(vid_path, coord_path, k, self.config, [], [], None)
            

            if video.getOnlyFrame() is None:
                messagebox.showerror("Invalid Adress", "Invalid video source!, Please type again", parent = self.window)
                return

            self.videos.append(video)

            self.config["video_sources"].append(vid_path)
            self.config["points_sources"].append(coord_path)

            self.addLabel(video.video_source, k)
            
    

    def drawLines(self, idx):
        idx = int(idx)
        video = self.videos[idx]
        print(idx)
        self.PaintApp = PaintApp(tk.Toplevel(self.window), video.getOnlyFrame(), video.point_source )
        self.PaintApp.window.wm_attributes("-topmost", 1)