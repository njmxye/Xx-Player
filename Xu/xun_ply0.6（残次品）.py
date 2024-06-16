import os
import cv2
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import threading
import ffmpeg
from queue import Queue

class VideoPlayer(tk.Tk):
    """
    视频播放器类，继承自tk.Tk类，用于创建一个多视频播放器窗口。

    参数：
    - folder：视频文件夹的路径

    属性：
    - folder：视频文件夹的路径
    - video_files：视频文件列表
    - total_duration：所有视频的总时长
    - video_durations：每个视频的时长列表
    - current_video_index：当前播放的视频索引
    - current_position：当前播放的位置
    - resolution：视频的分辨率
    - scale：视频的缩放比例
    - canvas：用于显示视频帧的画布
    - progress：进度条控件
    - play_button：播放/停止按钮
    - resolution_label：分辨率标签
    - resolution_options：分辨率选项列表
    - resolution_var：分辨率选项的变量
    - resolution_menu：分辨率选项菜单
    - scale_slider：缩放比例滑块
    - stop_flag：停止标志
    - frame_queue：视频帧队列
    """

    def __init__(self, folder):
        super().__init__()
        self.title("小寻播放器v0.6")
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
        
        self.resolution_options = ["640x480", "800x600", "1920x1080"]
        self.resolution_var = tk.StringVar(value=self.resolution_options[0])
        self.resolution_menu = ttk.OptionMenu(self, self.resolution_var, self.resolution_options[0], *self.resolution_options, command=self.change_resolution)
        self.resolution_menu.pack()
        
        self.scale_slider = ttk.Scale(self, orient='horizontal', length=640, from_=0.1, to=2.0, value=1.0, command=self.on_scale_change)
        self.scale_slider.pack()
        
        self.stop_flag = threading.Event()
        self.frame_queue = Queue()  # Queue to hold processed frames
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def calculate_durations(self):
        """
        计算每个视频的时长，并累加得到总时长。
        """
        for video in self.video_files:
            filepath = os.path.join(self.folder, video)
            probe = ffmpeg.probe(filepath)
            duration = float(probe['format']['duration'])
            self.video_durations.append(duration)
            self.total_duration += duration

    def change_resolution(self, resolution):
        """
        更改视频的分辨率。

        参数：
        - resolution：新的分辨率，格式为"宽x高"
        """
        self.resolution = resolution
        width, height = map(int, resolution.split('x'))
        self.canvas.config(width=width, height=height)

    def on_scale_change(self, value):
        """
        当缩放比例滑块的值发生变化时调用。

        参数：
        - value：新的缩放比例值
        """
        self.scale = float(value)

    def play_video(self):
        """
        播放视频，启动视频处理线程。
        """
        self.stop_flag.clear()
        self.play_button.config(text="Stop", command=self.stop_video)
        threading.Thread(target=self.process_videos).start()

    def stop_video(self):
        """
        停止视频播放。
        """
        self.stop_flag.set()
        self.play_button.config(text="Play", command=self.play_video)

    def process_videos(self):
        """
        处理视频文件，将视频帧放入帧队列。
        """
        cap = cv2.VideoCapture()
        try:
            for video in self.video_files:
                filepath = os.path.join(self.folder, video)
                cap.open(filepath)
                while cap.isOpened() and not self.stop_flag.is_set():
                    ret, frame = cap.read()
                    if not ret:
                        break

                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame)

                    # Resize frame according to both resolution and scale
                    width, height = map(int, self.resolution.split('x'))
                    img = img.resize((int(width * self.scale), int(height * self.scale)), Image.ANTIALIAS)
                    self.frame_queue.put(img)

                    if self.frame_queue.qsize() > 100:  # Don't let the queue get too big
                        self.frame_queue.get()

            # If we finish one video, prepare for the next if there is one
            if not self.stop_flag.is_set():
                self.current_video_index += 1
                if self.current_video_index >= len(self.video_files):
                    self.current_video_index = 0
                    self.current_position = 0
                else:
                    self.process_videos()  # Start processing the next video
        finally:
            cap.release()

    def update_gui(self):
        """
        更新GUI，显示视频帧。
        """
        while not self.frame_queue.empty():
            img = self.frame_queue.get()
            imgtk = ImageTk.PhotoImage(image=img)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
            self.canvas.imgtk = imgtk  # Store reference to avoid garbage collection

        self.update_idletasks()
        if not self.stop_flag.is_set():
            self.after(10, self.update_gui)  # Update GUI every 10ms

    def update_progress(self):
        """
        更新进度条的位置。
        """
        self.progress.set(self.current_position)

    def on_progress_change(self, value):
        """
        当进度条的值发生变化时调用，更新当前播放的位置。

        参数：
        - value：新的进度条值
        """
        new_position = float(value)
        if new_position < self.current_position:
            self.current_video_index = 0
            self.current_position = 0

        while new_position > self.current_position + self.video_durations[self.current_video_index]:
            self.current_position += self.video_durations[self.current_video_index]
            self.current_video_index += 1

        self.current_position = new_position

    def on_closing(self):
        """
        关闭窗口时调用，停止视频播放。
        """
        self.stop_flag.set()
        self.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="选择需要处理的文件夹")
    root.destroy()
    if folder_path:
        player = VideoPlayer(folder_path)
        player.mainloop()