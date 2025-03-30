from PyQt6.QtWidgets import QApplication, QMainWindow #, QFileDialog
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6 import uic

import numpy as np
import pyaudio as pa
import wave
import sys

# 錄音需要的參數
form = pa.paInt16 # 16bit PCM格式
chan = 1 #聲道數
rate = 44100 # CD標準sample rate
chunk = 1024 # 緩衝區大小

#狀態對應文本
stat_text_dic = {"running": "錄音中... ", "pause": "錄音暫停 ", "stop": "錄音完成，點擊儲存以存成wav檔 "}


# 錄音thread
class Recorder_Th(QThread):
    # 3個event signal
    done = pyqtSignal(bytes)
    update_timer = pyqtSignal(float)
    rec_paused = pyqtSignal(bool)
    def __init__(self):
        super().__init__()
        self.running = False
        self.paused = False
        self.frames = []
        self.second = 0
        self.status = ""
    # 錄音
    def run(self):
        self.running = True
        self.frames = []
        self.second = 0
        audio = pa.PyAudio()
        stream = audio.open(format = form, channels = chan, rate = rate, input = True, frames_per_buffer = chunk)
        while self.running:
            if self.paused == True:
                self.status = "pause"
                self.update_timer.emit(self.second)
                continue
            self.status = "running"
            data = stream.read(chunk)
            self.frames.append(data)
            self.second += float(chunk/rate)
            self.update_timer.emit(self.second)
        stream.stop_stream()
        stream.close()
        audio.terminate()
        self.done.emit(b''.join(self.frames))
        self.status = "stop"
        self.update_timer.emit(self.second)
    # 暫停
    def pause(self):
        self.paused = not self.paused
        self.rec_paused.emit(self.paused)
    # 停止
    def stop(self):
        self.running = False
# UI
class Recorder_UI(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("recorder.ui", self)  # 載入 UI 檔案
        self.setWindowTitle("MyGO!!!!!")  # 修改視窗標題
        self.rec_th = None
        self.audioData = None
        #self.timer = QTimer()
        #self.timer.timeout.connect(self.set_time_text)
        # 綁button
        self.start_button.clicked.connect(self.start_rec)
        self.pause_button.clicked.connect(self.pause_rec)
        self.stop_button.clicked.connect(self.stop_rec)
        self.save_button.clicked.connect(self.save_file)
        self.clear_button.clicked.connect(self.clear_data)
    # 開始
    def start_rec(self):
        self.label.setText("錄音中...")
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.save_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        # 錄音thread準備
        self.rec_th = Recorder_Th()
        self.rec_th.done.connect(self.rec_done) # signal連結function
        self.rec_th.update_timer.connect(self.set_time_text)
        self.rec_th.rec_paused.connect(self.on_pause)
        self.rec_th.start() #thread 啟動
    # 暫停
    def pause_rec(self):
        if self.rec_th:
            self.rec_th.pause()
    # 暫停UI處理
    def on_pause(self, paused):
        if paused:
            #self.label.setText("錄音暫停")
            self.pause_button.setText("繼續")
        else:
            #self.label.setText("錄音中...")
            self.pause_button.setText("暫停")
    # 停止
    def stop_rec(self):
        if self.rec_th:
            self.rec_th.stop()
            #self.label.setText("錄音完成，點擊儲存以存成wav檔")
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.stop_button.setEnabled(False)
    # 完成，接收thread錄好的資料
    def rec_done(self, data):
        self.audioData = data
        self.pause_button.setText("暫停")
        self.save_button.setEnabled(True)
        self.clear_button.setEnabled(True)
    # 儲存
    def save_file(self):
        filename = "audio"
        if self.filename_text.text() != '':
            filename = self.filename_text.text()
        filename += '.wav'
        with wave.open(filename, 'wb') as wf:
            audio = pa.PyAudio()
            wf.setnchannels(chan)
            wf.setsampwidth(audio.get_sample_size(form))
            wf.setframerate(rate)
            wf.writeframes(self.audioData)
        self.label.setText("儲存成功，臭ㄐㄐ")
    #清除
    def clear_data(self):
        self.audioData = None
        self.save_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.label.setText("點擊開始以開始錄音")
        self.filename_text.setText('')
    # Timer
    def set_time_text(self, sec):
        self.label.setText(stat_text_dic[self.rec_th.status] + "%.2f"%sec + " 秒")

if __name__ == "__main__":
    app = QApplication([])
    window = Recorder_UI()
    window.show()
    app.exec()