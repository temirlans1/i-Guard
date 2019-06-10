import tkinter as tk
import time
import subprocess, os, platform
from database import Database
class Notifications():
    def __init__(self, parent, database,  from_db = False, db_data = None, filepath = ""):
        
        self.filepath = filepath
        self.db = database
        
        if from_db:
            (self.id, self.filepath, self.status, self.created_time) = db_data
        else:
            (self.id, self.status, self.created_time) = database.insert(filepath)

        strtime = time.strftime('%H:%M:%S, %d.%m.%Y', time.localtime(self.created_time))
        
        color = "white"
        if not self.status:
            color = 'light coral'


        #font = tkFont.Font(family="Helvetica",size=36,weight="bold")
        
        self.button = tk.Button(parent, text = strtime, bg = color, relief = tk.FLAT, height = 4, width = 20,
                                 font = ("Helvetica", 10), fg = "black")
        self.button.configure(command = self.on_pressed)
        self.button.bind("<Enter>", self.on_enter)
        self.button.bind("<Leave>", self.on_leave)
    
    def on_enter(self, e):
        color = "tomato"
        if self.status:
            color = 'gainsboro'
        self.button.configure(bg = color)


    def on_leave(self, e):
        color = "light coral"
        if self.status:
            color = 'white'
        self.button.configure(bg = color)


    def on_pressed(self):
        if self.status == False:
            self.db.update_status(self.id)
            self.status = True
            self.button.configure(bg = 'white')

        if platform.system() == 'Darwin':       # macOS
            subprocess.call(('open', self.filepath))
        elif platform.system() == 'Windows':    # Windows
            os.startfile(self.filepath)
        else:                                   # linux variants
            subprocess.call(('xdg-open', self.filepath))
    
        
    