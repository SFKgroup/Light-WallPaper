from PyQt5.QtWebEngineWidgets import QWebEngineView,QWebEngineSettings,QWebEnginePage
from PyQt5.Qt import QUrl,QIcon
import PyQt5.QtCore
from PyQt5.QtWidgets import QListWidget,QGridLayout,QPushButton,QSystemTrayIcon,QMenu,QAction,QMessageBox,QLineEdit,QInputDialog
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWidgets import  QWidget, QApplication
from PyQt5.QtGui import  QFontDatabase , QFont
import win32gui,win32con,win32api
import os
import sys
import json
from pynput.mouse import Listener
import requests
import qtawesome
from urllib.parse import urlparse

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
    "name":"动态壁纸",
    "font":f"{filepath}/Alibaba-PuHuiTi-Regular.otf",
    "font_size":15,
    "width":480,
    "height":640,
    "theme_colour":"#39C5BB",
    "auto_apply":True,
    "show_home":True,
    "block_home":False,
    "block_set":False
}

if not os.path.isfile(filepath+'config.json'):
    with open(filepath+'config.json','w',encoding='utf-8') as g:g.write(json.dumps(setting))

with open(filepath+'config.json','r',encoding='utf-8') as g:setting.update(json.loads(g.read()))
with open(filepath+'config.json','w',encoding='utf-8') as g:g.write(json.dumps(setting))

if not os.path.isfile(setting['icon']):
    import mkicon
    mkicon.mkicon(setting['icon'])

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

class Background(QWidget):
    global setting

    def __init__(self):
        global hwnd_background
        super(Background, self).__init__()
        self.setObjectName("MainWindow")
        self.resize(1920, 1080)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setEnabled(True)

        # webviewer初始化
        size = self.geometry()
        self.viewer = WebEngineView(self)
        self.viewer.resize(size.width(),size.height())
        self.viewer.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True) 
        self.viewer.load(QUrl(setting["page"]))
        self.viewer.show()
        self.viewer.setZoomFactor(setting["zoom"])

        # 设置为壁纸
        win_hwnd = int(self.winId())
        win32gui.SetParent(win_hwnd, hwnd_background)

        # 监听鼠标事件(由于窗口位置在桌面下方,因此需要监听桌面的鼠标点击,然后转发给窗口)
        self.listener = Listener(on_click=self.on_click)
        self.listener.start()

    def on_click(self,x, y, button, pressed):
        global hwnd_WorkW
        if win32gui.GetForegroundWindow() != hwnd_WorkW:return None
        if pressed and str(button) == 'Button.left':
            #print(button,'鼠标点击在 ({0}, {1})'.format(x, y))
            pos = win32api.MAKELONG(x, y)
            win32api.SendMessage(self.winId(), win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, pos)
            win32api.SendMessage(self.winId(), win32con.WM_LBUTTONUP, None, pos)

    def quit(self):
        self.listener.stop()
        self.close()

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
        self.setWindowTitle(setting['name'])
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
        self.button_add.setText("添加壁纸")
        self.button_add.clicked.connect(self.add_background)
        self.button_add.setFont(QFont(self.fontFamily,setting['font_size'],QFont.Black))
        self.button_add.setStyleSheet('QPushButton{color:#EEE;background-color:#313131;padding: 7px 15px;}QPushButton:hover{background:#111;color:'+setting["theme_colour"]+'}')
        self.layouter.addWidget(self.button_add)

        self.button_apply = QPushButton()
        self.button_apply.setText("应用壁纸")
        self.button_apply.clicked.connect(self.apply_background)
        self.button_apply.setFont(QFont(self.fontFamily,setting['font_size'],QFont.Black))
        self.button_apply.setStyleSheet('QPushButton{color:#EEE;background-color:#313131;padding: 7px 15px;}QPushButton:hover{background:#111;color:'+setting["theme_colour"]+'}')
        self.layouter.addWidget(self.button_apply)

        self.button_remove = QPushButton()
        self.button_remove.setText("还原壁纸")
        self.button_remove.clicked.connect(self.close_background)
        self.button_remove.setFont(QFont(self.fontFamily,setting['font_size'],QFont.Black))
        self.button_remove.setStyleSheet('QPushButton{color:#EEE;background-color:#313131;padding: 7px 15px;}QPushButton:hover{background:#111;color:'+setting["theme_colour"]+'}')
        self.layouter.addWidget(self.button_remove)

        self.button_set = QPushButton()
        self.button_set.setText("设置")
        self.button_set.clicked.connect(self.global_set)
        self.button_set.setFont(QFont(self.fontFamily,setting['font_size'],QFont.Black))
        self.button_set.setStyleSheet('QPushButton{color:#EEE;background-color:#313131;padding: 7px 15px;}QPushButton:hover{background:#111;color:'+setting["theme_colour"]+'}')
        self.layouter.addWidget(self.button_set)

        self.button_del = QPushButton()
        self.button_del.setText("删除壁纸")
        self.button_del.clicked.connect(self.del_background)
        self.button_del.setFont(QFont(self.fontFamily,setting['font_size'],QFont.Black))
        self.button_del.setStyleSheet('QPushButton{color:#EEE;background-color:#412121;padding: 7px 15px;}QPushButton:hover{background:#111;color:'+setting["theme_colour"]+'}')
        self.layouter.addWidget(self.button_del)

        # 托盘菜单
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(setting['icon']))
        self.icon_menu = QMenu()
        if not setting['block_home']:
            action_show  = QAction(qtawesome.icon('fa.home', color='white'), '显示主页', self, triggered=self.show)
            self.icon_menu.addAction(action_show)
        action_quit  = QAction(qtawesome.icon('fa.sign-out', color='white'), '退出软件', self, triggered=sys.exit)
        self.icon_menu.addAction(action_quit)
        action_bgon  = QAction(qtawesome.icon('fa.toggle-on', color='white'), '开启壁纸', self, triggered=self.apply_background)
        self.icon_menu.addAction(action_bgon)
        action_bgoff = QAction(qtawesome.icon('fa.window-close-o', color='white'), '关闭壁纸', self, triggered=self.close_background)
        self.icon_menu.addAction(action_bgoff)
        self.icon_menu.setStyleSheet('QMenu{color:#DDD;background-color:#222;selection-color:'+setting["theme_colour"]+'}')
        self.tray_icon.setContextMenu(self.icon_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.show_window)

        if setting['auto_apply']:self.apply_background()

    def show_window(self, reason):
        if (reason == 2 or reason == 3) and not setting['block_home']:self.show()

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
            msgBox.setText(f'设置已锁定')
            msgBox.setWindowTitle("警告")
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
        msgBox.setText(f'您确定要删除标签:"{item.text()}"吗?')
        msgBox.setWindowTitle("警告")
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
        with open(filepath+'config.json','w',encoding='utf-8') as g:g.write(json.dumps(setting))

    def add_background(self):
        self.input_window = input_window()
        self.input_window.show()

    def apply_background(self):
        self.close_background()
        try:
            if not setting["page"]:
                msgBox = QMessageBox()
                msgBox.setWindowIcon(QIcon(setting["icon"]))
                msgBox.setIcon(QMessageBox.Critical)
                msgBox.setText(f'无选中壁纸标签')
                msgBox.setWindowTitle("错误")
                msgBox.setStandardButtons(QMessageBox.Ok)
                msgBox.exec()
                return None
            self.bg_on_flag = True
            self.wall_paper = Background()
            self.wall_paper.show()
            with open(filepath+'config.json','w',encoding='utf-8') as g:g.write(json.dumps(setting))
        except Exception as e:log(e)

    def close_background(self):
        if self.bg_on_flag:self.wall_paper.quit()

    def closeEvent(self, event):
        self.tray_icon.showMessage(setting['name'], f'{setting["name"]}已经最小化到系统托盘', QIcon(setting['icon']))

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
        self.setWindowTitle(setting['name'])
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
        self.line_name.setPlaceholderText("标签名称")
        self.line_name.setFont(QFont(self.fontFamily,setting['font_size'],QFont.Black))
        self.layouter.addWidget(self.line_name)

        self.line_url = QLineEdit(self)
        self.line_url.setStyleSheet('QLineEdit{color:#EEE;background-color:#313131;padding: 7px 15px;}')
        self.line_url.setPlaceholderText("壁纸URL或绝对路径")
        self.line_url.setFont(QFont(self.fontFamily,setting['font_size'],QFont.Black))
        self.layouter.addWidget(self.line_url)

        self.line_exe = QLineEdit(self)
        self.line_exe.setStyleSheet('QLineEdit{color:#EEE;background-color:#313131;padding: 7px 15px;}')
        self.line_exe.setPlaceholderText("预启动文件")
        self.line_exe.setFont(QFont(self.fontFamily,setting['font_size'],QFont.Black))
        self.layouter.addWidget(self.line_exe)

        self.button_ok = QPushButton()
        self.button_ok.setText("添加壁纸")
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
            msgBox.setText(f'标签名称不能为空')
            msgBox.setWindowTitle("错误")
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            return None
        elif name in setting['page_dic'].keys():
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QIcon(setting["icon"]))
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setText(f'您确定要覆盖标签:"{name}"的设置吗?')
            msgBox.setWindowTitle("警告")
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            returnValue = msgBox.exec()
            if returnValue == QMessageBox.Cancel:return None
        if not dic['url']:
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QIcon(setting["icon"]))
            msgBox.setIcon(QMessageBox.Critical)
            msgBox.setText(f'壁纸链接不能为空')
            msgBox.setWindowTitle("错误")
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            return None
        if dic['exe'] and not os.path.isfile(dic['exe']):
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QIcon(setting["icon"]))
            msgBox.setIcon(QMessageBox.Critical)
            msgBox.setText(f'您指定的预启动文件不存在')
            msgBox.setWindowTitle("错误")
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
        with open(filepath+'config.json','w',encoding='utf-8') as g:g.write(json.dumps(setting))
        setting["page"] = setting["page_dic"][name]["url"]
        setting["start_up"] = setting["page_dic"][name]["exe"]
        main_window.listwidget.clear()
        for item in setting["page_dic"].keys():main_window.listwidget.addItem(item)
        self.close()

class setting_window(QWidget):
    global setting

    def __init__(self):
        global main_window,UI_STYLE

        QWidget.__init__(self)
        # 输出控件
        self.layouter = QGridLayout()
        self.setLayout(self.layouter)

        self.setWindowOpacity(setting['alpha'])
        self.setWindowIcon(QIcon(setting["icon"]))
        self.setWindowTitle(setting['name'])
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
            "show_home":"启动显示主页"
        }
        self.zh_opt = dict(zip(self.opt_zh.values(), self.opt_zh.keys()))
        self.listwidget = QListWidget()
        for key in setting.keys():
            if not key in self.opt_zh.keys():continue
            self.listwidget.addItem(f'{self.opt_zh[key]}: {setting[key]}')
        self.listwidget.clicked.connect(self.list_clicked)
        self.listwidget.setFont(QFont(self.fontFamily,setting['font_size'],QFont.Black))
        self.listwidget.setStyleSheet('QListWidget{color:#EEE;background-color:#313131;padding: 7px 15px;}')
        self.layouter.addWidget(self.listwidget)


        self.button_ok = QPushButton()
        self.button_ok.setText("确认更改")
        self.button_ok.clicked.connect(self.apply_change)
        self.button_ok.setFont(QFont(self.fontFamily,setting['font_size'],QFont.Black))
        self.button_ok.setStyleSheet('QPushButton{color:#EEE;background-color:#313131;padding: 7px 15px;}QPushButton:hover{background:#111;color:'+setting["theme_colour"]+'}')
        self.layouter.addWidget(self.button_ok)

    def list_clicked(self, qmodelindex):
        item = self.listwidget.currentItem()
        key = item.text().split(':')[0]

        self.setStyleSheet('')
        value, ok = QInputDialog().getText(self,f'编辑:{key}', '新的值:')
        self.setStyleSheet(UI_STYLE)
        if not ok:
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QIcon(setting["icon"]))
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText(f'您的修改未成功')
            msgBox.setWindowTitle("提示")
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
            msgBox.setText(f'设置已锁定')
            msgBox.setWindowTitle("警告")
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
            self.close()
            return None
        if not self.temp_opt:
            self.close()
            return None
        setting.update(self.temp_opt)
        with open(filepath+'config.json','w',encoding='utf-8') as g:g.write(json.dumps(setting))
        self.close()

def log(data):
    if not os.path.isfile('./log,txt'):open('./log,txt','w').close()
    with open('./log,txt','a',encoding='utf-8') as g:g.write(f'[ERROR] {data}\n')

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
    #app.setStyle('Fusion')
    hwnd_background = pretreatmentHandle()

    main_window = Window()
    if setting['show_home'] and not setting['block_home']:main_window.show()

    sys.exit(app.exec_())