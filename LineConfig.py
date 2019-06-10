from tkinter import *
import tkinter.font
from PIL import ImageTk, Image
import json
import yaml
from tkinter import messagebox
import cv2
import math



class PaintApp:
 
    

    def save_and_quit(self):
        for i in range(self.line_count):
            self.data[i][0] = int(self.data[i][0] * self.ratio_x)
            self.data[i][1] = int(self.data[i][1] * self.ratio_y)
            self.data[i][2] = int(self.data[i][2] * self.ratio_x)
            self.data[i][3] = int(self.data[i][3] * self.ratio_y)

        with open(self.readFile, "w") as readFile:
            yaml.dump(self.data, readFile)
        self.window.destroy()

    
    # Tracks x & y when the mouse is clicked and released
    
    def erase_last_line(self):
        if(self.line_count>0):
            self.data.pop(self.line_count-1)
            self.drawing_area.delete(self.idx[self.line_count-1])
            self.line_count -= 1

    # ---------- CATCH MOUSE UP ----------
 
    def left_but_down(self, event=None):
        print("Pressed in " + str(event.x) + " " + str(event.y))
        # Set x & y when mouse is clicked
        self.x1_line_pt = event.x
        self.y1_line_pt = event.y
        self.pressed = TRUE
        self.idx[self.line_count] = self.drawing_area.create_line(0, 0, 0, 0, smooth=TRUE, fill="green", width = 5)
        
    # ---------- CATCH MOUSE UP ----------
 
    def motion(self, event=None):
        if self.pressed and None not in (self.x1_line_pt, self.y1_line_pt, event.x, event.y):
            self.drawing_area.coords(self.idx[self.line_count], self.x1_line_pt, self.y1_line_pt, event.x, event.y)

    def left_but_up(self, event=None):
        
        self.pressed = FALSE
        # Reset the line
        self.x2_line_pt = event.x
        self.y2_line_pt = event.y
        coords = [ self.x1_line_pt, self.y1_line_pt, self.x2_line_pt, self.y2_line_pt ]
        if math.sqrt((self.x1_line_pt-self.x2_line_pt)**2 + (self.y1_line_pt-self.y2_line_pt)**2) > 25:
            self.data[self.line_count] = coords
            self.line_count += 1
        else :
            self.drawing_area.delete(self.idx[self.line_count])
        #self.drawing_area.create_line(self.x1_line_pt, self.y1_line_pt, self.x2_line_pt, self.y2_line_pt, smooth=TRUE, fill="green", width = 5)
        # Set x & y when mouse is released
        
 
    def __init__(self, window, frame, readFile):
        y, x, _ = frame.shape
        filename = ImageTk.PhotoImage(image = Image.fromarray(cv2.cvtColor(cv2.resize(frame, (1000, 600)), cv2.COLOR_BGR2RGB)))
        
        self.ratio_x = x / 1000
        self.ratio_y = y / 600

        self.readFile = readFile
        self.window = window
        self.data = {}
        self.pressed = FALSE

        self.x1_line_pt, self.y1_line_pt, self.x2_line_pt, self.y2_line_pt = None, None, None, None

        self.idx = {}
        self.line_count = 0

        drawing_area = Canvas(self.window, height=filename.height(), width=filename.width() + 100)
        drawing_area.create_image(0, 0, image = filename, anchor = NW)
        #self.idx = drawing_area.create_line(0, 0, 0, 0, smooth=TRUE, fill="green", width = 5)
        button1 = Button(drawing_area, text = "Save", command = self.save_and_quit, anchor = W)
        button1.configure(width = 10, activebackground = "#33B5E5", relief = FLAT)
        button1_window = drawing_area.create_window(filename.width(), 10, anchor=NW, window=button1)
        
        button2 = Button(drawing_area, text = "Back", command = self.erase_last_line, anchor = W)
        button2.configure(width = 10, activebackground = "#33B5E5", relief = FLAT)
        button2_window = drawing_area.create_window(filename.width(), 50, anchor=NW, window=button2)


        drawing_area.bind("<Motion>", self.motion)
        drawing_area.bind("<ButtonPress-1>", self.left_but_down)
        drawing_area.bind("<ButtonRelease-1>", self.left_but_up)
        drawing_area.pack(fill = BOTH, expand = True)
        
        self.filename = filename
        self.drawing_area = drawing_area
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Warning! All unsaved changings will be deleted. Do you want to continue?", parent = self.window):
            self.window.destroy()
        else :
            pass
