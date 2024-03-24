# LightWallPaper : 一个轻量化的HTML壁纸引擎

## LightWallPaper : A light HTML wallpaper engine

### 一、Introduction 简介

​	**LightWallPaper**是一个轻量化的HTML壁纸引擎。其设计的初衷是为了帮助开发者将自己的实用性壁纸做成一个独立的软件。这些壁纸往往除去装饰作用外，还可以用于提升生产力等多个方面，很多开发者想要将其独立地做成一个产品。但限于在当下实现此类功能往往需要*Wallpaper Engine*等软件，需要用户单独安装，而无法将自己的HTML壁纸从其中独立出来，本项目正是为了解决该问题而生的。

### 二、Characteristic 特色

​	**LightWallPaper**相较于其它壁纸引擎的不同之处在于以下几点：

- 可以被打包成为单文件形式
- 可以在启动时在后台隐藏地启动预设的可执行文件(`.exe`,`.bat`,`.vbs`...)
- 单文件打包后小于 200 MB
- 不会显示网络上其它壁纸等诸多其它服务，界面简单
- 使用json格式存储设置，方便修改
- 窗体图标与名称均支持自定义

### 三、Usage 使用

​	双击即可运行程序。程序首次运行会生成`.\config\config.json`,`.\config\language.json`和`.\config\favicon.ico`三个个必需的文件。其中`.\config\config.json`为设置文件，完整内容如下：

```json
{
    "start_up": "./http-server.exe",  // 启动时自动在后台启动的可执行文件，可留空
    "page": "http://127.0.0.1:8080",  // 启动时自动显示的壁纸的URL
    "page_dic": {    // 可用的壁纸列表
        "测试服务器": {   // 壁纸在UI显示的标签名称
            "url": "http://127.0.0.1:8080",  // 该壁纸的URL
            "exe": "./http-server.exe"       // 启动该壁纸时需要执行的文件(启动路径)
        },
        "百度一下": {
            "url": "http://www.baidu.com",
            "exe": ""
        }
    },
    "zoom": 1.25,   // HTML壁纸在WebViewer的缩放
    "alpha": 0.9,   // UI窗口的透明度
    "icon": "./config//favicon.ico",  // 窗口图标的路径(必须存在,否则无法在系统托盘创建图标)
    "font": "./config//Alibaba-PuHuiTi-Regular.otf",  // UI的字体(此处建议阿里巴巴普惠体)，可以留空
    "font_size": 15,  // UI的字符大小
    "width": 480,     // UI主页窗口的宽
    "height": 640,    // UI主页窗口的高
    "theme_colour": "#39C5BB",  // 鼠标移动到按键上显示的颜色
    "auto_apply": true,  // 启动时自动显示壁纸
    "show_home": true,   // 启动时自动显示主页
    "block_home": false, // 禁用显示主页
    "block_set": false   // 锁定UI界面的设置项修改功能
    "clear_storage": false,  // 在下次启动时清除缓存
    "storage_path": "",      // 缓存目录(启动后自动设定)
    "auto_clear_level": 3,   // 清除等级(cookie,浏览记录,完全重置)
    "auto_clear_rate": 24,   // 自动清除频率(单位:小时)
    "last_clear_time": 1710677659.4013422,   // 上一次执行自动清除的时间(自动更新)
    "guide_time": 3,        // 壁纸窗口位置检测周期(单位:秒)
    "guide_reload": false,  // 是否刷新长时间无活动页面(无CPU和IO活动)
    "debug_mode": false,    // 是否开启浏览器debug
    "debug_port": 5566      // 浏览器debug端口
}
```

​	首次运行生成的config文件中会包含有两个用于测试的HTML壁纸。如果要通过修改config来设置壁纸，请在`page_dic`里添加或删除你的壁纸，`start_up`和`page`会随你选中并应用壁纸而修改。

​	壁纸支持使用文件路径作为URL，但是适应性较差*(可能会受路径中存在的特定字符影响)*，强烈建议将壁纸文件放在本地的文件服务器上(会在release里自带一个)，使用本地回环地址`http://127.0.0.1`进行访问，较为稳定。本地服务器的可执行文件若在启动时需要传参的，可以先写成`.bat`文件，之后将config中的启动路径设为`.bat`文件的路径。

​	`.\config\language.json`为语言文件，键为不同位置的文本，值为文本的替换内容。目前有的版本如下：(`zh-cn`,`en-us`)使用不同语言文件替换`.\config\language.json`即可完成语言的切换。

### 四、Build 编译打包

​	使用pyinstaller将本程序打包为exe:

```bash
pyinstaller main.py -F -i favicon.ico -w -n LightWallPaper 
```

​	请不要使用`upx`进行压缩，在调试过程中发现，由于未知原因，有些版本的代码在使用upx压缩编译后的可执行文件无法正常地显示WebViewer，可以使用upx压缩的版本会在版本说明里进行备注。



### 五、Plan 更新计划

- [x] 将UI中的中文提取成为单独的文件
- [ ] 优化内置icon文件的存储方式(目前偷懒,保存为了Base64字符串)
- [ ] 提高软件的可调节性，开放更多UI风格调节的选项
- [ ] 优化URL输入时的协议自动补全