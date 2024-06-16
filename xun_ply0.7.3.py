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
        self.title("多视频播放器")
        self.geometry("800x600")

        self.folder = folder
        self.video_files = self.get_video_files()
        self.total_duration = self.calculate_total_duration()
        self.current_video_index = 0
        self.current_position = 0
        self.resolution = "640x480"
        self.scale = 1.0

        self.canvas = self.create_canvas()
        self.progress = self.create_progress_bar()
        self.play_button = self.create_play_button()
        self.resolution_menu = self.create_resolution_menu()
        self.scale_slider = self.create_scale_slider()
        self.stop_flag = threading.Event()
        self.speed = 1.0
        self.speed_label = self.create_speed_label()
        self.speed_slider = self.create_speed_slider()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def get_video_files(self):
        video_files = [f for f in os.listdir(self.folder) if f.endswith(('mp4', 'avi', 'mkv'))]
        video_files.sort()
        return video_files

    def calculate_total_duration(self):
        total_duration = 0
        for video in self.video_files:
            filepath = os.path.join(self.folder, video)
            probe = ffmpeg.probe(filepath)
            duration = float(probe['format']['duration'])
            total_duration += duration
        return total_duration

    def create_canvas(self):
        canvas = tk.Canvas(self, width=640, height=480)
        canvas.pack()
        return canvas

    def create_progress_bar(self):
        progress = ttk.Scale(self, orient='horizontal', length=640, from_=0, to=self.total_duration,
                             command=self.on_progress_change)
        progress.pack()
        return progress

    def create_play_button(self):
        play_button = tk.Button(self, text="播放", command=self.play_video)
        play_button.pack()
        return play_button

    def create_resolution_menu(self):
        resolution_label = tk.Label(self, text="选择分辨率:")
        resolution_label.pack()

        resolution_options = ["640x480", "800x600", "1850x900"]
        resolution_var = tk.StringVar(value=resolution_options[0])
        resolution_menu = ttk.OptionMenu(self, resolution_var, resolution_options[0], *resolution_options,
                                         command=self.change_resolution)
        resolution_menu.pack()
        return resolution_menu

    def create_scale_slider(self):
        scale_slider = ttk.Scale(self, orient='horizontal', length=640, from_=0.1, to=2.0, value=1.0,
                                 command=self.on_scale_change)
        scale_slider.pack()
        return scale_slider

    def create_speed_label(self):
        speed_label = tk.Label(self, text="播放速度: 1.0x")
        speed_label.pack()
        return speed_label

    def create_speed_slider(self):
        speed_slider = ttk.Scale(self, orient='horizontal', length=640, from_=0.001, to=1000.0, value=1.0,
                                command=self.change_speed)
        speed_slider.pack()
        return speed_slider

    def change_resolution(self, resolution):
        self.resolution = resolution
        width, height = map(int, resolution.split('x'))
        self.canvas.config(width=width, height=height)

    def on_scale_change(self, value):
        self.scale = float(value)

    def play_video(self):
        self.stop_flag.clear()
        self.play_button.config(text="停止", command=self.stop_video)
        threading.Thread(target=self.play).start()

    def stop_video(self):
        self.stop_flag.set()
        self.play_button.config(text="播放", command=self.play_video)

    def play(self):
        cap = cv2.VideoCapture()

        while not self.stop_flag.is_set():
            video = self.video_files[self.current_video_index]
            filepath = os.path.join(self.folder, video)
            cap.open(filepath)

            frame_rate = cap.get(cv2.CAP_PROP_FPS)

            while cap.isOpened() and not self.stop_flag.is_set():
                ret, frame = cap.read()
                if not ret:
                    break
                self.current_position += 1 / (frame_rate * self.speed)
                self.update_progress()

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)

                width, height = map(int, self.resolution.split('x'))
                img = img.resize((int(width * self.scale), int(height * self.scale)), Image.ANTIALIAS)

                imgtk = ImageTk.PhotoImage(image=img)
                self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                self.canvas.imgtk = imgtk

                self.update_idletasks()

                delay = int(1000 / (frame_rate * self.speed))
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

    def change_speed(self, speed):
        self.speed = float(speed)
        self.speed_label.config(text=f"播放速度: {self.speed}x")


class SkinVideoPlayer(VideoPlayer):
    def __init__(self, folder, skin):
        super().__init__(folder)
        self.skin = skin

    def create_canvas(self):
        canvas = self.skin.create_canvas(self, width=640, height=480)
        canvas.pack()
        return canvas

    def create_progress_bar(self):
        progress = self.skin.create_progress_bar(self, orient='horizontal', length=640, from_=0,
                                                 to=self.total_duration, command=self.on_progress_change)
        progress.pack()
        return progress

    def create_play_button(self):
        play_button = self.skin.create_play_button(self, text="播放", command=self.play_video)
        play_button.pack()
        return play_button

    def create_resolution_menu(self):
        resolution_label = self.skin.create_label(self, text="选择分辨率:")
        resolution_label.pack()

        resolution_options = ["640x480", "800x600", "1850x900"]
        resolution_var = tk.StringVar(value=resolution_options[0])
        resolution_menu = self.skin.create_option_menu(self, resolution_var, resolution_options[0],
                                                       *resolution_options, command=self.change_resolution)
        resolution_menu.pack()
        return resolution_menu

    def create_scale_slider(self):
        scale_slider = self.skin.create_scale_slider(self, orient='horizontal', length=640, from_=0.1, to=2.0,
                                                     value=1.0, command=self.on_scale_change)
        scale_slider.pack()
        return scale_slider

    def create_speed_label(self):
        speed_label = self.skin.create_label(self, text="播放速度: 1.0x")
        speed_label.pack()
        return speed_label

    def create_speed_slider(self):
        speed_slider = self.skin.create_speed_slider(self, orient='horizontal', length=640, from_=0.001, to=1000.0,
                                                     value=1.0, command=self.change_speed)
        speed_slider.pack()
        return speed_slider


class Skin:
    def create_canvas(self, master, **kwargs):
        return tk.Canvas(master, **kwargs)

    def create_progress_bar(self, master, **kwargs):
        return ttk.Scale(master, **kwargs)

    def create_play_button(self, master, **kwargs):
        return tk.Button(master, **kwargs)

    def create_label(self, master, **kwargs):
        return tk.Label(master, **kwargs)

    def create_option_menu(self, master, **kwargs):
        return ttk.OptionMenu(master, **kwargs)

    def create_scale_slider(self, master, **kwargs):
        return ttk.Scale(master, **kwargs)

    def create_speed_slider(self, master, **kwargs):
        return ttk.Scale(master, **kwargs)


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="选择包含视频的文件夹")
    root.destroy()
    if folder_path:
        player = SkinVideoPlayer(folder_path, Skin())
        player.mainloop()
