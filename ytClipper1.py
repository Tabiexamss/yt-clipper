from pytube import YouTube
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.editor import TextClip, concatenate_videoclips
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QVBoxLayout, QPushButton, QLabel, QSlider, QListWidget, QListWidgetItem, QMessageBox, QWidget, QProgressBar, QInputDialog, QLineEdit, QAction, QDockWidget
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import Qt, QUrl, QThread, pyqtSignal
import random
import os
import logging

# Set up logging
logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')

class ClipMaker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(list)

    def __init__(self, video, output_directory, video_duration, title, subtitle):
        super().__init__()
        self.video = video
        self.output_directory = output_directory
        self.video_duration = video_duration
        self.title = title
        self.subtitle = subtitle

    def run(self):
        clip_start_times = list(range(0, self.video_duration, 55))
        random.shuffle(clip_start_times)
        clips = []

        for i, start_time in enumerate(clip_start_times):
            clip_duration = random.randint(30, 55)
            end_time = start_time + clip_duration if start_time + clip_duration < self.video_duration else self.video_duration
            clip_filename = os.path.join(self.output_directory, f'clip_{i}.mp4')
            ffmpeg_extract_subclip(self.video, start_time, end_time, targetname=clip_filename)
            # Add title and subtitle to the clip
            clip = moviepy.editor.VideoFileClip(clip_filename)
            title_clip = TextClip(self.title, fontsize=24, color='white').set_duration(clip.duration).set_position(('center', 'top'))
            subtitle_clip = TextClip(self.subtitle, fontsize=24, color='white').set_duration(clip.duration).set_position(('center', 'bottom'))
            final_clip = concatenate_videoclips([clip, title_clip, subtitle_clip])
            final_clip.write_videofile(clip_filename, codec='libx264')  # Overwrite the original clip
            clips.append((clip_filename, start_time, end_time))
            self.progress.emit((i + 1) * 100 // len(clip_start_times))

        self.finished.emit(clips)

class VideoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt Video Player Widget Example")
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.videowidget = QVideoWidget()
        self.mediaPlayer.setVideoOutput(self.videowidget)
        self.setCentralWidget(self.videowidget)
        self.clip_list = QListWidget()
        self.clip_list.itemDoubleClicked.connect(self.play_clip)
        self.clip_list.itemClicked.connect(self.edit_clip)
        self.clip_list_dock = QDockWidget("Clips", self)
        self.clip_list_dock.setWidget(self.clip_list)
        self.addDockWidget(Qt.RightDockWidgetArea, self.clip_list_dock)
        self.progress_bar = QProgressBar()
        self.statusBar().addPermanentWidget(self.progress_bar)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter title here")
        self.subtitle_input = QLineEdit()
        self.subtitle_input.setPlaceholderText("Enter subtitle here")
        self.menuBar().setCornerWidget(self.title_input, Qt.TopLeftCorner)
        self.menuBar().setCornerWidget(self.subtitle_input, Qt.TopRightCorner)
        self.save_action = QAction("Save All Clips", self)
        self.save_action.triggered.connect(self.save_all_clips)
        self.menuBar().addAction(self.save_action)
        self.start_action = QAction("Start", self)
        self.start_action.triggered.connect(self.start_clip_maker)
        self.menuBar().addAction(self.start_action)

    def load_video(self, video):
        self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(video)))
        self.mediaPlayer.play()

    def play_clip(self, item):
        self.load_video(item.data(Qt.UserRole)[0])

    def edit_clip(self, item):
        clip_filename, start_time, end_time = item.data(Qt.UserRole)
        new_start_time, ok = QInputDialog.getInt(self, "Edit Clip", "Start Time:", start_time, 0, self.mediaPlayer.duration() / 1000)
        if ok:
            new_end_time, ok = QInputDialog.getInt(self, "Edit Clip", "End Time:", end_time, new_start_time, self.mediaPlayer.duration() / 1000)
            if ok:
                ffmpeg_extract_subclip(self.video, new_start_time, new_end_time, targetname=clip_filename)
                item.setData(Qt.UserRole, (clip_filename, new_start_time, new_end_time))

    def add_clips(self, clips):
        for clip in clips:
            item = QListWidgetItem(os.path.basename(clip[0]))
            item.setData(Qt.UserRole, clip)
            self.clip_list.addItem(item)

    def save_all_clips(self):
        for i in range(self.clip_list.count()):
            item = self.clip_list.item(i)
            clip_filename, start_time, end_time = item.data(Qt.UserRole)
            # Save the clip
            # ...

    def start_clip_maker(self):
        youtube_url, ok = QInputDialog.getText(None, "YouTube URL", "Enter the YouTube video URL:")
        if not ok:
            return
        output_directory = QFileDialog.getExistingDirectory(None, "Select the directory to save the video and clips")
        youtube = YouTube(youtube_url)
        video = youtube.streams.get_highest_resolution().download(output_path=output_directory)
        video_duration = youtube.length
        self.load_video(video)  # Load the video into the GUI
        clip_maker = ClipMaker(video, output_directory, video_duration, self.title_input.text(), self.subtitle_input.text())
        clip_maker.progress.connect(self.progress_bar.setValue)
        clip_maker.finished.connect(self.add_clips)
        clip_maker.start()

def main():
    # Create a PyQt5 application object
    app = QApplication([])

    player = VideoPlayer()
    player.resize(640, 480)
    player.show()

    # Execute the application
    app.exec_()

if __name__ == "__main__":
    main()
