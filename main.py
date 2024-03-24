from PyQt5.QtWebEngineWidgets import QWebEngineView,QWebEngineSettings,QWebEnginePage, QWebEngineProfile
from PyQt5.Qt import QUrl,QIcon
import PyQt5.QtCore
from PyQt5.QtWidgets import QListWidget,QGridLayout,QPushButton,QSystemTrayIcon,QMenu,QAction,QMessageBox,QLineEdit,QInputDialog
from PyQt5.QtCore import QUrl, Qt, pyqtSignal ,QObject
from PyQt5.QtWidgets import  QWidget, QApplication
from PyQt5.QtGui import  QFontDatabase , QFont
import win32gui,win32con,win32api
from win32 import win32process
import os
import sys
import json
from pynput.mouse import Listener
import requests
import qtawesome
from urllib.parse import urlparse
import time
import psutil
import threading


DEBUG_PORT = '5588'
DEBUG_URL = 'http://127.0.0.1:%s' % DEBUG_PORT
os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = DEBUG_PORT

UI_STYLE = '''
    background:#242424;
    border-top:1px solid #444444;
    border-bottom:1px solid #444444;
    border-right:1px solid #444444;
    border-left:1px solid #444444;
    border-top-left-radius:10px;
    border-top-right-radius:10px;
    border-bottom-left-radius:10px;
    border-bottom-right-radius:10px;
'''

filepath = './config/'
if not os.path.exists(filepath):os.mkdir(filepath)

setting = {
    "start_up":"./http-server.exe",
    "page":"http://127.0.0.1:8080",
    "page_dic":{
        "测试服务器":{"url":"http://127.0.0.1:8080","exe":"./http-server.exe"},
        "百度一下":{"url":"http://www.baidu.com" ,"exe":""}
    },
    "zoom":1.25,
    "alpha":0.9,
    "icon":f"{filepath}/favicon.ico",
    "font":f"{filepath}/Alibaba-PuHuiTi-Regular.otf",
    "font_size":15,
    "width":480,
    "height":640,
    "theme_colour":"#39C5BB",
    "auto_apply":True,
    "show_home":True,
    "block_home":False,
    "block_set":False,
    "clear_storage":False,
    "storage_path":"",
    "auto_clear_level":3,
    "auto_clear_rate":24,
    "last_clear_time":0,
    "guide_time":3,
    "guide_reload":True
}

language = {
    'name':'动态壁纸',
    'add_wp' : '添加壁纸',
    'del_wp' : '删除壁纸',
    'apply_wp' : '应用壁纸',
    'restore_wp' : '还原壁纸',
    'setting' : '设置',
    'close' : '退出软件',
    'home' : '显示主页',
    'apply' : '确认更改',
    'warnning' : '警告',
    'error' : '错误',
    'setting_block' : '设置已锁定',
    'sure_del' : '您确定要删除标签',
    'wp_empty' : '无选中壁纸标签',
    'has_min' : '已经最小化到系统托盘',
    'tag_name' : '标签名称',
    'wp_url' : '壁纸URL或绝对路径',
    'wp_startup' : '预启动文件',
    'unsuccessful' : '您的修改未成功',
    'edit' : '编辑',
    'del_cache' : '清除缓存',
    'new_value' : '新的值',
    'non_empty_name' : '标签名称不能为空',
    'non_empty_url' : '壁纸链接不能为空',
    'notfound' : '您指定的预启动文件不存在',
    'sure_cover' : '您确定要覆盖标签',
    'sentting_of' : '的设置吗',
    'opt' : {
            'zoom':'网页缩放(0~2)',
            'alpha':'主页透明度(0~1)',
            'font':'字体文件路径',
            'font_size':'字体大小',
            "width":'主页窗口宽度',
            "height":'主页窗口高度',
            "theme_colour":"主题色(#十六进制)",
            "auto_apply":"自动接管壁纸",
            "show_home":"启动显示主页",
            "guide_reload":"自动刷新无活动页面"
        }
}

if not os.path.isfile(filepath+'config.json'):
    with open(filepath+'config.json','w',encoding='utf-8') as g:g.write(json.dumps(setting, indent=4))

with open(filepath+'config.json','r',encoding='utf-8') as g:setting.update(json.loads(g.read()))
with open(filepath+'config.json','w',encoding='utf-8') as g:g.write(json.dumps(setting, indent=4))

if not os.path.isfile(setting['icon']):
    import mkicon
    mkicon.mkicon(setting['icon'])

if not os.path.isfile(filepath+'language.json'):
    with open(filepath+'language.json','w',encoding='utf-8') as g:g.write(json.dumps(language, indent=4,ensure_ascii=False))

with open(filepath+'language.json','r',encoding='utf-8') as g:language.update(json.loads(g.read()))

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
    global setting

    def __init__(self,url = None):
        global hwnd_background
        super(Background, self).__init__()
        self.setObjectName("MainWindow")
        self.setWindowTitle(language['name']+'_Background')
        self.resize(1920, 1080)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setEnabled(True)

        # webviewer初始化
        size = self.geometry()
        self.viewer = WebEngineView(self)
        self.viewer.resize(size.width(),size.height())
        self.viewer.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True)
        if url:
            self.viewer.load(QUrl(url))
            print(url)
        else:self.viewer.load(QUrl(setting["page"]))
        self.viewer.setZoomFactor(setting["zoom"])

        #self.viewer.show()

        # 设置为壁纸
        hwnd_background = pretreatmentHandle()
        self.win_hwnd = int(self.winId())
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
                win32gui.SetParent(self.control.win_hwnd, hwnd_background)
                log(f"New parent window : {hwnd_background}",msg_type='INFO')
                
    def stop(self):
        self.if_stop = True

# 主页
class Window(QWidget):
    global setting

    def __init__(self):
        global UI_STYLE
        QWidget.__init__(self)
        # 输出控件
        self.layouter = QGridLayout()
        self.setLayout(self.layouter)

        self.setWindowOpacity(setting['alpha'])
        self.setWindowIcon(QIcon(setting["icon"]))
        self.setWindowTitle(language['name'])
        self.resize(setting['width'], setting['height'])
        self.bg_on_flag = False

        self.setStyleSheet(UI_STYLE)

        # 加载字体
        fontDb = QFontDatabase()
        font = fontDb.applicationFontFamilies(fontDb.addApplicationFont(setting['font']))
        if font:self.fontFamily = font[0]
        else:self.fontFamily = None

        # 选择框
        self.listwidget = QListWidget()
        for item in setting["page_dic"].keys():self.listwidget.addItem(item)
        self.listwidget.clicked.connect(self.list_clicked)
        self.listwidget.setFont(QFont(self.fontFamily,setting['font_size'],QFont.Black))
        self.listwidget.setStyleSheet('QListWidget{color:#EEE;background-color:#313131;padding: 7px 15px;}')
        self.layouter.addWidget(self.listwidget)

        # 底部按钮
        self.button_add = QPushButton()
        self.button_add.setText(f" {language['add_wp']} ")
        self.button_add.clicked.connect(self.add_background)
        self.button_add.setFont(QFont(self.fontFamily,setting['font_size'],QFont.Black))
        self.button_add.setStyleSheet('QPushButton{color:#EEE;background-color:#313131;padding: 7px 15px;}QPushButton:hover{background:#111;color:'+setting["theme_colour"]+'}')
        self.layouter.addWidget(self.button_add)

        self.button_apply = QPushButton()
        self.button_apply.setText(f" {language['apply_wp']} ")
        self.button_apply.clicked.connect(self.apply_background)
        self.button_apply.setFont(QFont(self.fontFamily,setting['font_size'],QFont.Black))
        self.button_apply.setStyleSheet('QPushButton{color:#EEE;background-color:#313131;padding: 7px 15px;}QPushButton:hover{background:#111;color:'+setting["theme_colour"]+'}')
        self.layouter.addWidget(self.button_apply)

        self.button_remove = QPushButton()
        self.button_remove.setText(f" {language['restore_wp']} ")
        self.button_remove.clicked.connect(self.close_background)
        self.button_remove.setFont(QFont(self.fontFamily,setting['font_size'],QFont.Black))
        self.button_remove.setStyleSheet('QPushButton{color:#EEE;background-color:#313131;padding: 7px 15px;}QPushButton:hover{background:#111;color:'+setting["theme_colour"]+'}')
        self.layouter.addWidget(self.button_remove)

        self.button_set = QPushButton()
        self.button_set.setText(f" {language['setting']} ")
        self.button_set.clicked.connect(self.global_set)
        self.button_set.setFont(QFont(self.fontFamily,setting['font_size'],QFont.Black))
        self.button_set.setStyleSheet('QPushButton{color:#EEE;background-color:#313131;padding: 7px 15px;}QPushButton:hover{background:#111;color:'+setting["theme_colour"]+'}')
        self.layouter.addWidget(self.button_set)

        self.button_del = QPushButton()
        self.button_del.setText(f" {language['del_wp']} ")
        self.button_del.clicked.connect(self.del_background)
        self.button_del.setFont(QFont(self.fontFamily,setting['font_size'],QFont.Black))
        self.button_del.setStyleSheet('QPushButton{color:#EEE;background-color:#412121;padding: 7px 15px;}QPushButton:hover{background:#111;color:'+setting["theme_colour"]+'}')
        self.layouter.addWidget(self.button_del)

        # 托盘菜单
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(setting['icon']))
        self.icon_menu = QMenu()
        if not setting['block_home']:
            action_show  = QAction(qtawesome.icon('fa.home', color='white'), f'{language["home"]}', self, triggered=self.show)
            self.icon_menu.addAction(action_show)
        action_quit  = QAction(qtawesome.icon('fa.sign-out', color='white'), f'{language["close"]}', self, triggered=self.app_quit)
        self.icon_menu.addAction(action_quit)
        action_bgon  = QAction(qtawesome.icon('fa.toggle-on', color='white'), f'{language["apply_wp"]}', self, triggered=self.apply_background)
        self.icon_menu.addAction(action_bgon)
        action_bgoff = QAction(qtawesome.icon('fa.window-close-o', color='white'), f'{language["restore_wp"]}', self, triggered=self.close_background)
        self.icon_menu.addAction(action_bgoff)
        self.icon_menu.setStyleSheet('QMenu{color:#DDD;background-color:#222;selection-color:'+setting["theme_colour"]+'}')
        self.tray_icon.setContextMenu(self.icon_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.show_window)

        self.wall_paper = None
        if setting['auto_apply']:self.apply_background()

    def show_window(self, reason):
        if (reason == 2 or reason == 3) and not setting['block_home']:self.show()

    def app_quit(self):
        if self.wall_paper:self.wall_paper.quit()
        if self.process_monitor:self.process_monitor.stop()
        QApplication.quit()

    def list_clicked(self, qmodelindex):
        global setting
        item = self.listwidget.currentItem()
        setting["page"] = setting["page_dic"][item.text()]["url"]
        setting["start_up"] = setting["page_dic"][item.text()]["exe"]

    def global_set(self):
        if setting["block_set"]:
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QIcon(setting["icon"]))
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setText(f'{language["setting_block"]}')
            msgBox.setWindowTitle(f"{language['warnning']}")
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            return None
        self.set_window = setting_window()
        self.set_window.show()

    def del_background(self):
        item = self.listwidget.currentItem()
        if not item:return None
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QIcon(setting["icon"]))
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setText(f'{language["sure_del"]}:"{item.text()}"?')
        msgBox.setWindowTitle(f"{language['warnning']}")
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        returnValue = msgBox.exec()
        if returnValue == QMessageBox.Cancel:return None
        else:del setting["page_dic"][item.text()]
        self.listwidget.clear()
        for item in setting["page_dic"].keys():self.listwidget.addItem(item)
        if setting["page_dic"]:
            setting["page"]     = setting["page_dic"][list(setting["page_dic"].keys())[0]]["url"]
            setting["start_up"] = setting["page_dic"][list(setting["page_dic"].keys())[0]]["exe"]
        else:setting["page"] = setting["start_up"] = ""
        with open(filepath+'config.json','w',encoding='utf-8') as g:g.write(json.dumps(setting, indent=4))

    def add_background(self):
        self.input_window = input_window()
        self.input_window.show()

    def apply_background(self,url = None):
        self.close_background()
        try:
            if not setting["page"]:
                msgBox = QMessageBox()
                msgBox.setWindowIcon(QIcon(setting["icon"]))
                msgBox.setIcon(QMessageBox.Critical)
                msgBox.setText(f'{language["wp_empty"]}')
                msgBox.setWindowTitle(f"{language['error']}")
                msgBox.setStandardButtons(QMessageBox.Ok)
                msgBox.exec()
                return None
            self.bg_on_flag = True
            self.wall_paper = Background(url = url)
            self.wall_paper.show()
            self.process_monitor = ProcessMonitor(self.wall_paper)
            self.process_monitor.start()
            
            with open(filepath+'config.json','w',encoding='utf-8') as g:g.write(json.dumps(setting, indent=4))

            self.process_monitor.signal.connect(self.apply_background)
        except Exception as e:log(e)

    def close_background(self):
        if self.bg_on_flag and self.wall_paper:
            self.wall_paper.quit()
            self.process_monitor.stop()

    def closeEvent(self, event):
        self.tray_icon.showMessage(language['name'], f'{language["name"]} {language["has_min"]}', QIcon(setting['icon']))

# 新建壁纸窗口
class input_window(QWidget):
    global setting

    def __init__(self):
        global main_window,UI_STYLE

        QWidget.__init__(self)
        # 输出控件
        self.layouter = QGridLayout()
        self.setLayout(self.layouter)

        self.setWindowOpacity(setting['alpha'])
        self.setWindowIcon(QIcon(setting["icon"]))
        self.setWindowTitle(language['name'])
        self.resize(setting['width'], setting['height']//2)
        self.bg_on_flag = False

        self.setStyleSheet(UI_STYLE)

        # 加载字体
        fontDb = QFontDatabase()
        font = fontDb.applicationFontFamilies(fontDb.addApplicationFont(setting['font']))
        if font:self.fontFamily = font[0]
        else:self.fontFamily = None

        # 输入内容
        self.line_name = QLineEdit(self)
        self.line_name.setStyleSheet('QLineEdit{color:#EEE;background-color:#313131;padding: 7px 15px;}')
        self.line_name.setPlaceholderText(f"{language['tag_name']}")
        self.line_name.setFont(QFont(self.fontFamily,setting['font_size'],QFont.Black))
        self.layouter.addWidget(self.line_name)

        self.line_url = QLineEdit(self)
        self.line_url.setStyleSheet('QLineEdit{color:#EEE;background-color:#313131;padding: 7px 15px;}')
        self.line_url.setPlaceholderText(f"{language['wp_url']}")
        self.line_url.setFont(QFont(self.fontFamily,setting['font_size'],QFont.Black))
        self.layouter.addWidget(self.line_url)

        self.line_exe = QLineEdit(self)
        self.line_exe.setStyleSheet('QLineEdit{color:#EEE;background-color:#313131;padding: 7px 15px;}')
        self.line_exe.setPlaceholderText(f"{language['wp_startup']}")
        self.line_exe.setFont(QFont(self.fontFamily,setting['font_size'],QFont.Black))
        self.layouter.addWidget(self.line_exe)

        self.button_ok = QPushButton()
        self.button_ok.setText(f"{language['add_wp']}")
        self.button_ok.clicked.connect(self.apply_change)
        self.button_ok.setFont(QFont(self.fontFamily,setting['font_size'],QFont.Black))
        self.button_ok.setStyleSheet('QPushButton{color:#EEE;background-color:#313131;padding: 7px 15px;}QPushButton:hover{background:#111;color:'+setting["theme_colour"]+'}')
        self.layouter.addWidget(self.button_ok)

    def apply_change(self):
        global main_window
        dic = {}
        dic['url'] = self.line_url.text()
        dic['exe'] = self.line_exe.text()
        name = self.line_name.text()
        # 输入过滤
        if not name:
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QIcon(setting["icon"]))
            msgBox.setIcon(QMessageBox.Critical)
            msgBox.setText(f'{language["non_empty_name"]}')
            msgBox.setWindowTitle(f"{language['error']}")
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            return None
        elif name in setting['page_dic'].keys():
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QIcon(setting["icon"]))
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setText(f'{language["sure_cover"]}:"{name}"{language["sentting_of"]}?')
            msgBox.setWindowTitle(f"{language['warnning']}")
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            returnValue = msgBox.exec()
            if returnValue == QMessageBox.Cancel:return None
        if not dic['url']:
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QIcon(setting["icon"]))
            msgBox.setIcon(QMessageBox.Critical)
            msgBox.setText(f'{language["non_empty_url"]}')
            msgBox.setWindowTitle(f"{language['error']}")
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            return None
        if dic['exe'] and not os.path.isfile(dic['exe']):
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QIcon(setting["icon"]))
            msgBox.setIcon(QMessageBox.Critical)
            msgBox.setText(f'{language["notfound"]}')
            msgBox.setWindowTitle(f"{language['error']}")
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Close)
            returnValue = msgBox.exec()
            if returnValue == QMessageBox.Ok:return None
            else:
                self.close()
                return None
            
        prase = urlparse(dic['url'])
        if os.path.isfile(dic['url']) and not prase.scheme:dic['url'] = 'file:///' + str(os.path.abspath(dic['url'])).replace('\\','/')
        elif not prase.netloc and not prase.scheme:dic['url'] = 'http://' + dic['url']

        setting['page_dic'][name] = dic
        with open(filepath+'config.json','w',encoding='utf-8') as g:g.write(json.dumps(setting, indent=4))
        setting["page"] = setting["page_dic"][name]["url"]
        setting["start_up"] = setting["page_dic"][name]["exe"]
        main_window.listwidget.clear()
        for item in setting["page_dic"].keys():main_window.listwidget.addItem(item)
        self.close()

# 设置窗口
class setting_window(QWidget):
    global setting

    def __init__(self):
        global main_window,UI_STYLE,language

        QWidget.__init__(self)
        # 输出控件
        self.layouter = QGridLayout()
        self.setLayout(self.layouter)

        self.setWindowOpacity(setting['alpha'])
        self.setWindowIcon(QIcon(setting["icon"]))
        self.setWindowTitle(language['name'])
        self.resize(setting['width'], setting['height'])
        self.bg_on_flag = False

        self.setStyleSheet(UI_STYLE)

        # 加载字体
        fontDb = QFontDatabase()
        font = fontDb.applicationFontFamilies(fontDb.addApplicationFont(setting['font']))
        if font:self.fontFamily = font[0]
        else:self.fontFamily = None

        # 选项 ['zoom', 'alpha', 'icon', 'name', 'font', 'font_size', 'width', 'height', 'theme_colour', 'auto_apply', 'show_home']
        self.temp_opt = setting
        self.opt_zh = {
            'zoom':'网页缩放(0~2)',
            'alpha':'主页透明度(0~1)',
            'font':'字体文件路径',
            'font_size':'字体大小',
            "width":'主页窗口宽度',
            "height":'主页窗口高度',
            "theme_colour":"主题色(#十六进制)",
            "auto_apply":"自动接管壁纸",
            "show_home":"启动显示主页",
            "auto_clear_level":"自动清理等级",
            "auto_clear_rate":"自动清理频率(单位:小时)"
        }
        self.opt_zh.update(language['opt'])
        self.zh_opt = dict(zip(self.opt_zh.values(), self.opt_zh.keys()))
        self.listwidget = QListWidget()
        for key in setting.keys():
            if not key in self.opt_zh.keys():continue
            self.listwidget.addItem(f'{self.opt_zh[key]}: {setting[key]}')
        self.listwidget.clicked.connect(self.list_clicked)
        self.listwidget.setFont(QFont(self.fontFamily,setting['font_size'],QFont.Black))
        self.listwidget.setStyleSheet('QListWidget{color:#EEE;background-color:#313131;padding: 7px 15px;}')
        self.layouter.addWidget(self.listwidget)

        self.button_del = QPushButton()
        self.button_del.setText(f"{language['del_cache']}")
        self.button_del.clicked.connect(self.clear_data)
        self.button_del.setFont(QFont(self.fontFamily,setting['font_size'],QFont.Black))
        self.button_del.setStyleSheet('QPushButton{color:#EEE;background-color:#313131;padding: 7px 15px;}QPushButton:hover{background:#111;color:'+setting["theme_colour"]+'}')
        self.layouter.addWidget(self.button_del)

        self.button_ok = QPushButton()
        self.button_ok.setText(f"{language['apply']}")
        self.button_ok.clicked.connect(self.apply_change)
        self.button_ok.setFont(QFont(self.fontFamily,setting['font_size'],QFont.Black))
        self.button_ok.setStyleSheet('QPushButton{color:#EEE;background-color:#313131;padding: 7px 15px;}QPushButton:hover{background:#111;color:'+setting["theme_colour"]+'}')
        self.layouter.addWidget(self.button_ok)

    def clear_data(self):
        clear_cache(setting['auto_clear_level'],True)

    def list_clicked(self, qmodelindex):
        item = self.listwidget.currentItem()
        key = item.text().split(':')[0]

        self.setStyleSheet('')
        value, ok = QInputDialog().getText(self,f'{language["edit"]}:{key}', f'{language["new_value"]}:')
        self.setStyleSheet(UI_STYLE)
        if not ok:
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QIcon(setting["icon"]))
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText(f'{language["unsuccessful"]}')
            msgBox.setWindowTitle(f"{language['warnning']}")
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            return None
        
        if   self.zh_opt[key] in ['zoom', 'alpha']:value = float(value)
        elif self.zh_opt[key] in ['font_size', 'width', 'height']:value = round(float(value))
        elif self.zh_opt[key] in ['auto_apply', 'show_home']:value = value == 'True' or value == 'true' or value == '1'
        elif self.zh_opt[key] == "theme_colour" and value[0] != '#':value = '#' + value
        self.temp_opt[self.zh_opt[key]] = value

        self.listwidget.clear()
        for key in setting.keys():
            if not key in self.opt_zh.keys():continue
            self.listwidget.addItem(f'{self.opt_zh[key]}: {setting[key]}')


    def apply_change(self):
        if setting["block_set"]:
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QIcon(setting["icon"]))
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setText(f'{language["setting_block"]}')
            msgBox.setWindowTitle(f"{language['warnning']}")
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            self.close()
            return None
        if not self.temp_opt:
            self.close()
            return None
        setting.update(self.temp_opt)
        with open(filepath+'config.json','w',encoding='utf-8') as g:g.write(json.dumps(setting, indent=4))
        self.close()

# LOG方法
def log(data,msg_type:str = 'ERROR'):
    if not os.path.isfile('./log.txt'):open('./log.txt','w').close()
    with open('./log.txt','a',encoding='utf-8') as g:g.write(f'[{time.strftime("%Y-%m-%d_%H:%M:%S",time.localtime(time.time()))}][{msg_type}] {data}\n')

# 遍历文件
def tree(dir_name) -> list:
    res = []
    for root, dirs, files in os.walk(dir_name):
        for file in files:
            res.append(file)

    return res

# 删除缓存
def clear_cache(clear_level : int,clear_now : bool=False):
    global setting
    profile = QWebEngineProfile.defaultProfile()

    if clear_level >= 1:profile.clearAllVisitedLinks()
    if clear_level >= 2:profile.clearHttpCache()
    if clear_level >= 3:
        setting["storage_path"] = profile.persistentStoragePath()
        if clear_now:setting["clear_storage"] = True
    setting['last_clear_time'] = time.time()
    with open(filepath+'config.json','w',encoding='utf-8') as g:g.write(json.dumps(setting, indent=4))

def if_clear_cache() -> bool:
    if time.time() - setting["last_clear_time"] >= 60*60*setting["auto_clear_rate"]:return True
    else:return False

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

if __name__ == "__main__":
    if (setting["clear_storage"] or (if_clear_cache() and setting["auto_clear_level"] >= 3)) and os.path.exists(setting["storage_path"]):
        try:
            for file in tree(setting["storage_path"]):os.remove(os.path.join(setting["storage_path"], file))
        except Exception as e:log(e)
        setting["clear_storage"] = False
        with open(filepath+'config.json','w',encoding='utf-8') as g:g.write(json.dumps(setting, indent=4))

    if setting["start_up"]:
        try:requests.get(setting['page'],timeout=3)
        except:
            if os.path.isfile(setting["start_up"]):
                #os.system(f'start {setting["start_up"]}')
                win32api.ShellExecute(0, 'open',setting["start_up"].replace("/","\\"), '', '.\\', 0)
            else:pass

    PyQt5.QtCore.QCoreApplication.setAttribute(PyQt5.QtCore.Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    if if_clear_cache():clear_cache(setting["auto_clear_level"])

    main_window = Window()
    if setting['show_home'] and not setting['block_home']:main_window.show()

    sys.exit(app.exec_())