from PyQt6.QtGui import QAction,QIcon
from PyQt6.QtWidgets import QListWidget,QGridLayout,QPushButton,QSystemTrayIcon,QMenu,QMessageBox,QLineEdit,QInputDialog
from PyQt6.QtWidgets import  QWidget, QApplication
from PyQt6.QtGui import  QFontDatabase , QFont
import pythoncom
import win32api
import os
import sys
import json
import requests
import qtawesome
from urllib.parse import urlparse

from utils import *
from bgengine import *

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
        self.really_close = False

        self.setStyleSheet(UI_STYLE)

        # 加载字体
        font = QFontDatabase.applicationFontFamilies(QFontDatabase.addApplicationFont(setting['font']))
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

        self.button_exit = QPushButton()
        self.button_exit.setText(f" {language['close']} ")
        self.button_exit.clicked.connect(self.app_quit)
        self.button_exit.setFont(QFont(self.fontFamily,setting['font_size'],QFont.Black))
        self.button_exit.setStyleSheet('QPushButton{color:#EEE;background-color:#313131;padding: 7px 15px;}QPushButton:hover{background:#111;color:'+setting["theme_colour"]+'}')
        self.layouter.addWidget(self.button_exit)


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
        if (reason == QSystemTrayIcon.ActivationReason.Trigger) and not setting['block_home']:self.show()

    def app_quit(self):
        self.really_close = True
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
        save('config',setting)
        #with open(filepath+'config.json','w',encoding='utf-8') as g:g.write(json.dumps(setting, indent=4))

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
            
            save('config',setting)

            self.process_monitor.signal.connect(self.apply_background)
        except Exception as e:log(e)

    def close_background(self):
        if self.bg_on_flag and self.wall_paper:
            self.wall_paper.quit()
            self.process_monitor.stop()

    def closeEvent(self, event):
        if not self.really_close:self.tray_icon.showMessage(language['name'], f'{language["name"]} {language["has_min"]}', QIcon(setting['icon']))

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
        #fontDb = QFontDatabase()
        font = QFontDatabase.applicationFontFamilies(QFontDatabase.addApplicationFont(setting['font']))
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
        save('config',setting)
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
        font = QFontDatabase.applicationFontFamilies(QFontDatabase.addApplicationFont(setting['font']))
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
            "auto_clear_rate":"自动清理频率(单位:小时)",
            "guide_reload":"自动刷新无活动页面"
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
        save('config',setting)
        self.close()

def main():
    global setting
    init()
    if (setting["clear_storage"] or (if_clear_cache() and setting["auto_clear_level"] >= 3)) and os.path.exists(setting["storage_path"]):
        try:
            for file in tree(setting["storage_path"]):os.remove(os.path.join(setting["storage_path"], file))
        except Exception as e:log(e)
        setting["clear_storage"] = False
        save('config',setting)

    if setting["start_up"]:
        try:requests.get(setting['page'],timeout=3)
        except:
            if os.path.isfile(setting["start_up"]):
                win32api.ShellExecute(0, 'open',setting["start_up"].replace("/","\\"), '', '.\\', 0)
            else:pass

    if setting["debug_mode"]:
        DEBUG_PORT = setting["debug_port"]
        DEBUG_URL = 'http://127.0.0.1:%s' % DEBUG_PORT
        os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = DEBUG_PORT

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    if if_clear_cache():clear_cache(setting["auto_clear_level"])

    main_window = Window()
    if setting['show_home'] and not setting['block_home']:main_window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()