from tkinter import *
import tkinter.font
from PIL import ImageTk, Image
import json
import yaml
from tkinter import messagebox


with open("params.yaml", "r") as readFile:
    data = yaml.load(readFile)
data = {}


class PaintApp:
 
    pressed = FALSE
    line_count = 0
    i = {}

    def save_and_quit(self):
        with open("params.yaml", "w+") as readFile:
            yaml.dump(data, readFile)
        w.quit()

    def erase_last_line(self):
        if(self.line_count>0):
            data.pop(self.line_count-1)
            w.delete(self.i[self.line_count-1])
            self.line_count -= 1
    # Tracks x & y when the mouse is clicked and released
    x1_line_pt, y1_line_pt, x2_line_pt, y2_line_pt = None, None, None, None
 
    # ---------- CATCH MOUSE UP ----------
 
    def left_but_down(self, event=None):
        print("Pressed in " + str(event.x) + " " + str(event.y))
        # Set x & y when mouse is clicked
        self.x1_line_pt = event.x
        self.y1_line_pt = event.y
        self.pressed = TRUE
        self.i[self.line_count] = w.create_line(0, 0, 0, 0, smooth=TRUE, fill="green", width = 5)
        
    # ---------- CATCH MOUSE UP ----------
 
    def motion(self, event=None):
        if self.pressed and None not in (self.x1_line_pt, self.y1_line_pt, event.x, event.y):
            w.coords(self.i[self.line_count], self.x1_line_pt, self.y1_line_pt, event.x, event.y)

    def left_but_up(self, event=None):
        self.pressed = FALSE
        # Reset the line
        self.x2_line_pt = event.x
        self.y2_line_pt = event.y
        coords = [ self.x1_line_pt, self.y1_line_pt, self.x2_line_pt, self.y2_line_pt ]
        data[self.line_count] = coords
        self.line_count += 1     
        #w.create_line(self.x1_line_pt, self.y1_line_pt, self.x2_line_pt, self.y2_line_pt, smooth=TRUE, fill="green", width = 5)
        # Set x & y when mouse is released
        
 
    def __init__(self, drawing_area):
        button1 = Button(drawing_area, text = "Save", command = self.save_and_quit, anchor = W)
        button1.configure(width = 10, activebackground = "#33B5E5", relief = FLAT)
        button1_window = drawing_area.create_window(filename.width(), 10, anchor=NW, window=button1)
        button2 = Button(drawing_area, text = "Back", command = self.erase_last_line, anchor = W)
        button2.configure(width = 10, activebackground = "#33B5E5", relief = FLAT)
        button2_window = drawing_area.create_window(filename.width(), 50, anchor=NW, window=button2)
        
        drawing_area.bind("<Motion>", self.motion)
        drawing_area.bind("<ButtonPress-1>", self.left_but_down)
        drawing_area.bind("<ButtonRelease-1>", self.left_but_up)


root = Tk()

filename = ImageTk.PhotoImage(Image.open("index.png"))
w = Canvas(root, height=filename.height(), width=filename.width() + 100)
w.create_image(0, 0, image = filename, anchor = NW)

def on_closing():
    if messagebox.askokcancel("Quit", "Warning! All unsaved changings will be deleted. Do you want to continue?"):
        root.destroy()
    else :
        pass

root.protocol("WM_DELETE_WINDOW", on_closing)

w.pack()
paint_app = PaintApp(w)

root.mainloop()