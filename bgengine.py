from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage,QWebEngineSettings
from PyQt6.QtWidgets import  QWidget
from PyQt6.QtCore import QUrl, Qt
import pythoncom
import win32gui,win32con,win32api
import json 
import time
from pynput.mouse import Listener
from PyQt6.QtCore import pyqtSignal ,QObject
from win32 import win32process
import psutil
import threading
from utils import *

# 浏览器
class WebEngineView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createWindow(self, windowType):
        newView = WebEngineView(self)
        newView.urlChanged.connect(self.onUrlChanged)
        return newView

    def acceptNavigationRequest(self, url, type, isMainFrame):
        if type == QWebEnginePage.NavigationTypeLinkClicked:
            self.load(url)
            return False
        return super().acceptNavigationRequest(url, type, isMainFrame)

    def onUrlChanged(self, url):
        self.setUrl(url)

# 壁纸窗口
class Background(QWidget):
    global setting,language

    def __init__(self,url = None):
        global hwnd_background
        super(Background, self).__init__()
        self.setObjectName("MainWindow")
        self.setWindowTitle(language['name']+'_Background')
        #self.setWindowIcon(QIcon(setting["icon"]))
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setEnabled(True)

        hwnd_background = pretreatmentHandle()
        rect = win32gui.GetWindowRect(hwnd_background)
        window_size = (rect[2] - rect[0],rect[3] - rect[1])
        self.resize(*window_size)

        # webviewer初始化
        size = self.geometry()
        self.viewer = WebEngineView(self)
        self.viewer.resize(size.width(),size.height())
        self.viewer.settings().setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        if url:self.viewer.load(QUrl(url))
        else:self.viewer.load(QUrl(setting["page"]))
        self.viewer.setZoomFactor(setting["zoom"])

        #self.viewer.show()

        # 设置为壁纸
        self.win_hwnd = int(self.winId())
        rect = win32gui.GetWindowRect(self.win_hwnd)
        qtsize = list(map(lambda x:round(x/(rect[2]/window_size[0])),window_size))
        self.resize(*qtsize)
        self.viewer.resize(*qtsize)
        win32gui.SetWindowPos(self.win_hwnd,None,*rect,0)
        win32gui.SetParent(self.win_hwnd, hwnd_background)


        # 监听鼠标事件(由于窗口位置在桌面下方,因此需要监听桌面的鼠标点击,然后转发给窗口)
        self.listener = Listener(on_click=self.on_click)
        self.listener.start()

    def on_click(self,x, y, button, pressed):
        global hwnd_WorkW
        if win32gui.GetForegroundWindow() != hwnd_WorkW:return None
        if pressed and str(button) == 'Button.left':
            pos = win32api.MAKELONG(x, y)
            win32api.SendMessage(self.winId(), win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, pos)
            win32api.SendMessage(self.winId(), win32con.WM_LBUTTONUP, None, pos)

       

    def quit(self):
        self.listener.stop()
        self.close()

# 进程监视器
class ProcessMonitor(QObject):
    global hwnd_background,setting
    signal = pyqtSignal(str)
    def __init__(self,control:Background) -> None:
        super(ProcessMonitor, self).__init__()
        self.process_id = win32process.GetWindowThreadProcessId(int(control.win_hwnd))[-1]
        self.process = None
        self.if_stop = False
        self.thread = threading.Thread(target=self.main)
        self.control = control
        self.IO = []
        self.CPU = []


    def get_process(self) -> bool:
        for process in psutil.process_iter():
            if process.pid == self.process_id:
                self.process = process
                return True
        return False
    
    def start(self):
        if not self.get_process():raise "Process not found"
        self.thread.start()

    def main(self):
        global hwnd_background,setting
        while True:
            if self.if_stop:break
            data = {}
            data["Memory"] = self.process.memory_info().rss
            data["PerCpu"] = self.process.cpu_percent()
            data["Status"] = self.process.status()
            data["IOdata"] = self.process.io_counters()
            self.IO.append(sum(list(data["IOdata"])))
            if len(self.IO) > 5:self.IO.pop(0)
            self.CPU.append(data["PerCpu"])
            if len(self.CPU) > 5:self.CPU.pop(0)
            if setting["guide_reload"] and len(self.IO) >= 5 and len(self.CPU) >= 5 and ((all(self.CPU[0] == item for item in self.CPU) and self.CPU[0] < 0.5 )or all(self.IO[0] == item for item in self.IO)):
                data["reload"] = [self.CPU[0], self.IO[0]]
                data["url"] = self.control.viewer.url().toString()
                log(json.dumps(data),msg_type='INFO')
                self.signal.emit(data["url"])#
            time.sleep(setting["guide_time"])
            children = []
            win32gui.EnumChildWindows(hwnd_background, lambda hwnd, param: param.append(hwnd), children)
            if not self.control.win_hwnd in children:
                hwnd_background = pretreatmentHandle()
                #print(self.control.win_hwnd,hwnd_background)
                try:
                    win32gui.SetParent(self.control.win_hwnd, hwnd_background)
                    log(f"New parent window : {hwnd_background}",msg_type='INFO')
                except Exception as e:log(f"window_hwnd error : {e}")
                
    def stop(self):
        self.if_stop = True

# 获取壁纸窗口句柄
def pretreatmentHandle():
    global hwnd_WorkW
    hwnd = win32gui.FindWindow("Progman", "Program Manager")
    win32gui.SendMessageTimeout(hwnd, 0x052C, 0, None, 0, 0x03E8)
    hwnd_WorkW = None
    while 1:
        hwnd_WorkW = win32gui.FindWindowEx(None, hwnd_WorkW, "WorkerW", None)
        if not hwnd_WorkW:continue
        hView = win32gui.FindWindowEx(hwnd_WorkW, None, "SHELLDLL_DefView", None)
        if not hView:continue
        h = win32gui.FindWindowEx(None, hwnd_WorkW, "WorkerW", None)
        while h:
            win32gui.SendMessage(h, 0x0010, 0, 0)  # WM_CLOSE
            h = win32gui.FindWindowEx(None, hwnd_WorkW, "WorkerW", None)
        break

    #print(h,hwnd,hwnd_WorkW,hView)
    return hwnd