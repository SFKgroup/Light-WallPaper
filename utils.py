from PyQt6.QtWebEngineCore import QWebEngineProfile
import os
import json
import time

# config 目录
filepath = './config/'
if not os.path.exists(filepath):os.mkdir(filepath)

# 配置文件格式
setting = {
    "start_up":"./http-server.exe",
    "page":"http://127.0.0.1:8080",
    "page_dic":{
        "测试服务器":{"url":"http://127.0.0.1:8080","exe":"./http-server.exe"},
        "百度一下":{"url":"http://www.baidu.com" ,"exe":""}
    },
    "zoom":1,
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
    "auto_clear_level":1,
    "auto_clear_rate":24,
    "last_clear_time":0,
    "guide_time":3,
    "guide_reload":False,
    "debug_mode":False,
    "debug_port":5566
}

# 语言文件格式
language = {
    "name":"动态壁纸",
    "add_wp" : "添加壁纸",
    "del_wp" : "删除壁纸",
    "apply_wp" : "应用壁纸",
    "restore_wp" : "还原壁纸",
    "setting" : "设置",
    "close" : "退出软件",
    "home" : "显示主页",
    "apply" : "确认更改",
    "warnning" : "警告",
    "error" : "错误",
    "setting_block" : "设置已锁定",
    "sure_del" : "您确定要删除标签",
    "wp_empty" : "无选中壁纸标签",
    "has_min" : "已经最小化到系统托盘",
    "tag_name" : "标签名称",
    "wp_url" : "壁纸URL或绝对路径",
    "wp_startup" : "预启动文件",
    "unsuccessful" : "您的修改未成功",
    "edit" : "编辑",
    "del_cache" : "清除缓存",
    "new_value" : "新的值",
    "non_empty_name" : "标签名称不能为空",
    "non_empty_url" : "壁纸链接不能为空",
    "notfound" : "您指定的预启动文件不存在",
    "sure_cover" : "您确定要覆盖标签",
    "sentting_of" : "的设置吗",
    "opt" : {
            "zoom":"网页缩放(0~2)",
            "alpha":"主页透明度(0~1)",
            "font":"字体文件路径",
            "font_size":"字体大小",
            "width":"主页窗口宽度",
            "height":"主页窗口高度",
            "theme_colour":"主题色(#十六进制)",
            "auto_apply":"自动接管壁纸",
            "show_home":"启动显示主页",
            "guide_reload":"自动刷新无活动页面",
            "auto_clear_level":"自动清理等级",
            "auto_clear_rate":"自动清理频率(单位:小时)"
        }
}

# 配置文件保存方法
def save(file_name,data):
    with open(f'{filepath}/{file_name}.json','w',encoding='utf-8') as g:g.write(json.dumps(data, indent=4,ensure_ascii=False))

# 配置文件初始化方法
def init():
    global setting,language
    if not os.path.isfile(filepath+'config.json'):save('config',setting)

    with open(filepath+'config.json','r',encoding='utf-8') as g:setting.update(json.loads(g.read()))
    save('config',setting)

    if not os.path.isfile(setting['icon']):
        import mkicon
        mkicon.mkicon(setting['icon'])

    if not os.path.isfile(filepath+'language.json'):
        save('language',language)
        #with open(filepath+'language.json','w',encoding='utf-8') as g:g.write(json.dumps(language, indent=4,ensure_ascii=False))

    with open(filepath+'language.json','r',encoding='utf-8') as g:language.update(json.loads(g.read()))

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
    global setting,filepath
    profile = QWebEngineProfile.defaultProfile()

    if clear_level >= 1:profile.clearAllVisitedLinks()
    if clear_level >= 2:profile.clearHttpCache()
    if clear_level >= 3:
        setting["storage_path"] = profile.persistentStoragePath()
        if clear_now:setting["clear_storage"] = True
    setting['last_clear_time'] = time.time()
    save('config',setting)

# 判断是否需要清除缓存
def if_clear_cache() -> bool:
    global setting
    if time.time() - setting["last_clear_time"] >= 60*60*setting["auto_clear_rate"]:return True
    else:return False

