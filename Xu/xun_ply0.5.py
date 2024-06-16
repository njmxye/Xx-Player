import os
import cv2
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import threading
import ffmpeg

class VideoPlayer(tk.Tk):
    def __init__(self, folder):
        super().__init__()
        self.title("Multi-Video Player")
        self.geometry("800x600")
        
        self.folder = folder
        self.video_files = [f for f in os.listdir(folder) if f.endswith(('mp4', 'avi', 'mkv'))]
        self.video_files.sort()
        
        self.total_duration = 0
        self.video_durations = []
        self.calculate_durations()
        
        self.current_video_index = 0
        self.current_position = 0
        self.resolution = "640x480"
        self.scale = 1.0
        
        self.canvas = tk.Canvas(self, width=640, height=480)
        self.canvas.pack()
        
        self.progress = ttk.Scale(self, orient='horizontal', length=640, from_=0, to=self.total_duration, command=self.on_progress_change)
        self.progress.pack()
        
        self.play_button = tk.Button(self, text="Play", command=self.play_video)
        self.play_button.pack()
        
        self.resolution_label = tk.Label(self, text="Select Resolution:")
        self.resolution_label.pack()
        
        self.resolution_options = ["640x480", "800x600", "1850x900"]
        self.resolution_var = tk.StringVar(value=self.resolution_options[0])
        self.resolution_menu = ttk.OptionMenu(self, self.resolution_var, self.resolution_options[0], *self.resolution_options, command=self.change_resolution)
        self.resolution_menu.pack()
        
        self.scale_slider = ttk.Scale(self, orient='horizontal', length=640, from_=0.1, to=2.0, value=1.0, command=self.on_scale_change)
        self.scale_slider.pack()
        
        self.stop_flag = threading.Event()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def calculate_durations(self):
        for video in self.video_files:
            filepath = os.path.join(self.folder, video)
            probe = ffmpeg.probe(filepath)
            duration = float(probe['format']['duration'])
            self.video_durations.append(duration)
            self.total_duration += duration

    def change_resolution(self, resolution):
        self.resolution = resolution
        width, height = map(int, resolution.split('x'))
        self.canvas.config(width=width, height=height)

    def on_scale_change(self, value):
        self.scale = float(value)

    def play_video(self):
        self.stop_flag.clear()
        self.play_button.config(text="Stop", command=self.stop_video)
        threading.Thread(target=self.play).start()

    def stop_video(self):
        self.stop_flag.set()
        self.play_button.config(text="Play", command=self.play_video)

    def play(self):
        cap = cv2.VideoCapture()
        
        while not self.stop_flag.is_set():
            video = self.video_files[self.current_video_index]
            filepath = os.path.join(self.folder, video)
            cap.open(filepath)
            
            frame_rate = cap.get(cv2.CAP_PROP_FPS)
            delay = int(1000 / frame_rate)
            
            while cap.isOpened() and not self.stop_flag.is_set():
                ret, frame = cap.read()
                if not ret:
                    break
                
                self.current_position += 1 / frame_rate
                self.update_progress()
                
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                
                # Resize frame according to both resolution and scale
                width, height = map(int, self.resolution.split('x'))
                img = img.resize((int(width * self.scale), int(height * self.scale)), Image.ANTIALIAS)
                
                imgtk = ImageTk.PhotoImage(image=img)
                self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                self.canvas.imgtk = imgtk  # Store reference to avoid garbage collection
                
                self.update_idletasks()
                self.after(delay)
                
                if self.current_position >= self.total_duration:
                    break
            
            cap.release()
            
            if self.current_video_index < len(self.video_files) - 1:
                self.current_video_index += 1
            else:
                self.current_video_index = 0
                self.current_position = 0

    def update_progress(self):
        self.progress.set(self.current_position)

    def on_progress_change(self, value):
        new_position = float(value)
        if new_position < self.current_position:
            self.current_video_index = 0
            self.current_position = 0
        
        while new_position > self.current_position + self.video_durations[self.current_video_index]:
            self.current_position += self.video_durations[self.current_video_index]
            self.current_video_index += 1
        
        self.current_position = new_position

    def on_closing(self):
        self.stop_flag.set()
        self.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="Select Folder with Videos")
    root.destroy()
    if folder_path:
        player = VideoPlayer(folder_path)
        player.mainloop()