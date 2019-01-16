#!/usr/bin/python3
# -*- coding: utf-8 -*-
from flask import Flask, render_template, make_response, request, Markup, Response 
import os, datetime, random, json, time, sys
from datetime import datetime
import serial_port, threading, queue
import sqlite
import signal
import argparse
sys.path.append('/home/pi/.local/lib/python3.5/site-packages')

MOCK = False
DEBUG = False
if len(sys.argv) > 1:
    for i in sys.argv:
        if i == '-mock':
            MOCK = True
        if i == '-debug':
            DEBUG = True

WINDOWS = False
import platform
if platform.system() == 'Windows':
    WINDOWS = True

if ((not WINDOWS) and (not MOCK)):
    import usb_camera
    from crontab import CronTab

temp, hum, ph, tds, co2, lvl = ('0', '0', '0', '0', '0', '0')
input_queue = queue.Queue(1)

# dbPeriod = 600 # seconds 
arrayLen = 10
requestPeriod = 1 # seconds
circularArray = [0] * arrayLen 
arrayPivot = 0 
# itemPeriod = dbPeriod / arrayLen # seconds

app = Flask(__name__)
sql = sqlite.Sqlite('./sensorsData.db')

#return index page
@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html", title='Главная')

#return measurements page
@app.route("/measurements")
def measurements():
    return render_template("measurements/measurements.html", title='Измерения', goback='/index')

#return temperature page with dynamic measurements
###############################################
@app.route("/measurements/temp")
def temp():
    template_data = {
        'title': "Температура",
        'goback': "/measurements",
        'label' : "Температура"
    }
    return render_template("measurements/temp.html", **template_data)

@app.route("/temp_measure")
def temp_meas():
    with lock:
        ret_val = str(temp)
    return ret_val

#################################################
#return pH page
@app.route("/measurements/ph")
def ph():
    template_data = {
            'title' : "Кислотность",
            'label' : "Уровень pH", 
            'goback': "/measurements",
    }
    return render_template("measurements/ph.html", **template_data)

@app.route("/ph_measure")
def ph_meas():
    with lock:
        ret_val = str(ph)
    return ret_val
#################################################
#return TDS updatePage
@app.route("/measurements/tds")
def tds():
    template_data = {
        'title': "Солёность",
        'goback': "/measurements",
        'label' : "Уровень солей"
    }
    return render_template("measurements/tds.html", **template_data)

@app.route("/tds_measure")
def tds_meas():
    with lock:
        ret_val = str(tds)
    return ret_val
#################################################
#return CO2 page
@app.route("/measurements/co2")
def co2():
    template_data =  {
        'title': "Углекислый газ",
        'goback': "/measurements",
        'label' : "CO2"
    }
    return render_template("measurements/co2.html", **template_data)

@app.route("/co2_measure")
def co2_meas():
    with lock:
        ret_val = str(co2)
    return ret_val
##################################################

#camera control
##################################################
@app.route("/camera")
def camera():
    if (WINDOWS == True):
        return render_template("camera/camera_windows.html", title='Камера', goback='/index')
    else:
        return render_template("camera/camera.html", title='Камера', goback='/index')

@app.route("/camera/photo")
def photo():
    return render_template("camera/photo.html", title='Фото', goback='/camera')

@app.route("/make_photo/<img>")
def make_photo(img):
    camera = usb_camera.PiCamera(0)
    if img == "img1":
        name = "img1.jpg"
    elif img == "img2":
        name = "img2.jpg"
    try:
        camera.capture("./static/img/" + name, resize=(500, 300)) #need to fix size
    except RuntimeError:
        print("Photo is not created")
        return make_response('', 403)
    else:
        return make_response('', 200)
    finally:
        print("Camera close") #test
        camera.close()

@app.route("/clear_photo")
def clear_photo():
    os.system("rm -f ./static/img/img*")
    return make_response('', 200)

@app.route("/camera/video")
def video():
    return render_template("camera/video.html", title='Видео', goback='/camera')

@app.route("/start_record")
def start_record():
    my_cron = CronTab(user="pi")
    for job in my_cron:
        if job.comment == "Growbox":
            return make_response('', 403)
    job = my_cron.new(command="/home/pi/Projects/Test1/GrowBox/usb_camera.py", comment="Growbox") #there will be new path
    job.hour.every(1)
    my_cron.write()
    return make_response('', 200)

@app.route("/finish_record")
def finish_record():
    my_cron = CronTab(user="pi")
    for job in my_cron:
        if job.comment == "Growbox":
            my_cron.remove(job)
            my_cron.write()
            return make_response('', 200)
    return make_response('', 403)

@app.route("/remove_frames")
def remove_frames():
    os.system("rm -f ~/Pictures/*")
    return make_response('', 200)

@app.route("/make_video")
def make_video():
    if len(os.listdir("/home/pi/Pictures")) != 0: 
        os.system("convert -delay 10 -loop 0 ~/Pictures/* ./static/img/animation.gif")
        return make_response('', 200)
    return make_response('', 403)

##################################################

#return setting of GrowBox
@app.route("/settings")
def settings():
    row = sql.selectActivity()
    data = Markup(row[0][0])
    return render_template("/settings/settings.html", jsonStr=data, title='Управление', goback='/index')

@app.route("/accept_settings", methods=["POST"])
def accept_setting():
    print(request)
    content = request.json
    print(content)
    input_queue.put(str(content))
    sql.updateActivity(str(content))
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
####################################################

@app.route("/teacher_settings", methods=["POST"])
def log_in():
    content = request.json
    passwd = content["passwd"]
    if passwd == "secret":
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
    return make_response('', 403)

@app.route("/teacher_page")
def teacher_page():
    return render_template('/settings/teacher_settings.html', title='Настройки', goback='/index')

@app.route("/time_settings")
def time_settings():
    return render_template('/settings/time_settings.html', title='Время и дата', goback='/teacher_page')

@app.route("/net_settings")
def net_settings():
    return render_template('/settings/net_settings.html', title='Сеть и обновления', goback='/teacher_page')

@app.route("/calibration_page")
def calibration_page():
    return render_template('/settings/calibration.html', title='Калибровка датчика pH', goback='/teacher_page')

@app.route("/login")
def secret_page():
    return render_template('/settings/login.html', title='Регистрация', goback='/index')

@app.route("/apply_net_settings", methods=["POST"])
def apply_net_settings():
    login = request.form["login"]
    passwd = request.form["passwd"]
    connect_flag = False
    with open("/etc/wpa_supplicant/wpa_supplicant.conf", "r+") as file:
        for line in file:
            if login in line:
                connect_flag = True
        if not connect_flag:
            file.write('\nnetwork={\n\tssid="'+ login +'"\n\tpsk="' + passwd + '"\n\tkey_mgmt=WPA-PSK\n}\n')
    if not connect_flag:
        os.system("wpa_cli -i wlan0 reconfigure")
    return render_template('/settings/net_settings.html', title='Сеть и обновления', goback='/teacher_page')

@app.route("/update_system")
def update_system():
    ret = os.system("echo Update") #testing
    #ret = os.system("git pull origin master") #uncomment to update
    if ret == 0:
        return make_response('', 200)
    else: 
        return make_response('', 403)

@app.route("/apply_time", methods=["POST"])
def apply_time():
    content = request.json
    datetime_set = content["set-date"] + ' ' + content["set-time"]
    print(datetime_set) #testing
    set_systime(datetime_set) #uncomment to set system time
    datetime_obj = datetime.strptime(datetime_set, "%Y-%m-%d %H:%M")
    fmt_datetime = {"setTime"  : datetime_obj.strftime("%a %b %d %H:%M:%S %Y")}
    print(fmt_datetime)
    input_queue.put(json.dumps(fmt_datetime))
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route("/calibration/<param>") 
def calibration(param):
    if param == "four":
        command = json.dumps({"calibrate" : 4})
        print(command)
        input_queue.put(command)
    if param == "seven":
        command = json.dumps({"calibrate" : 7})
        print(command)
        input_queue.put(command)
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

###################################################

#return charts page
@app.route("/charts")
def charts():
    return render_template("charts/charts.html", title='Журнал', goback='/index')

#return chart
@app.route("/charts/<param>")
def temp_chart(param):
    if param == 'temp':
        template_data = {'label': "Температура", 'banner': "температуры"}
        title = "Журнал температуры"
    if param == 'acidity':
        template_data = {'label': "Уровень кислотности pH", 'banner': "уровня кислотности pH"}
        title = "Журнал уровня кислотности"
    if param == 'saline':
        template_data = {'label': "Уровень солей", 'banner': "уровня солей"}
        title = "Журнал уровня солей"
    if param == 'carbon':
        template_data = {'label': "Уровень CO2", 'banner': "уровня CO2"}
        title = "Журнал концентрации углекислого газа"
    print(title)
    return render_template("charts/month_chart.html", param=param, title=title, goback='/charts', **template_data)

@app.route("/charts/draw_chart", methods=["POST"])
def draw_chart():
    if request.json:
        param = request.json['param']
        period = request.json['period']
        if period:
            if period == 'hour':
                error, data, labels = prepareHourData2Chart(param = [param])
            if period == 'day':
                error, data, labels = prepareDayData2Chart(param = [param])
            if period == 'week':
                error, data, labels = prepareWeekData2Chart(param = [param])
            if period == 'month':
                error, data, labels = prepareMonthData2Chart(param = [param])

            template_data = {'error': error, 'labels': labels, 'data': data, 'param': param}
            return json.dumps(template_data), 200, {'ContentType':'application/json'}

#return return page about plants
@app.route("/info")
def info():
    return render_template("info.html", title='Справка', goback='/index')

@app.route("/dynamicCharts")
def dynamicTemp():
    return render_template("dynamicCharts.html")

def prepareMonthData2Chart(param):
    now = int(datetime.timestamp(datetime.now()))
    monthEarlier = now - 2592000
    # error, data, labels = prepareData(param, monthEarlier, now, 2592000 / (requestPeriod * arrayLen))
    error, data, labels = prepareData(param, monthEarlier, now, 100)
    labels = [datetime.fromtimestamp(x).strftime("%d.%m") for x in labels]
    return error, data, labels

def prepareWeekData2Chart(param):
    now = int(datetime.timestamp(datetime.now()))
    weekEarlier = now - 604800
    # error, data, labels = prepareData(param, weekEarlier, now, 604800 / (requestPeriod * arrayLen))
    error, data, labels = prepareData(param, weekEarlier, now, 50)
    labels = [datetime.fromtimestamp(x).strftime("%d.%m %Hh") for x in labels]
    return error, data, labels

def prepareDayData2Chart(param):
    now = int(datetime.timestamp(datetime.now()))
    dayEarlier = now - 86400
    # error, data, labels = prepareData(param, dayEarlier, now, 86400 / (requestPeriod * arrayLen))
    error, data, labels = prepareData(param, dayEarlier, now, 20)
    labels = [datetime.fromtimestamp(x).strftime("%H:%M") for x in labels]
    return error, data, labels

def prepareHourData2Chart(param):
    now = int(datetime.timestamp(datetime.now()))
    hourEarlier = now - 3600
    # error, data, labels = prepareData(param, hourEarlier, now, 3600 / (requestPeriod * arrayLen))
    error, data, labels = prepareData(param, hourEarlier, now, 5)
    labels = [datetime.fromtimestamp(x).strftime("%H:%M") for x in labels]
    return error, data, labels

def prepareData(param, fromTime, toTime, limit):
    data = sql.selectSensors(param, fromTime = fromTime, toTime = toTime, limit = limit)

    #print('DATA length: '+str(len(data)))
    if len(data) == 0:
        error = "Нет данных"
        labels = ""
        data = []
    else:
        for i in data:
            print(i)
        error = False        
        prep = [x for x in zip(*data)]
        labels = prep[0]
        data = prep[1]
    return error, data, labels

def insertSensorsIntoDB(temp, hum, ph, tds, co2, lvl):
    global arrayPivot, arrayLen, circularArray

    circularArray[arrayPivot] = (float(temp), float(hum), float(ph), float(tds), float(co2))
    arrayPivot += 1 
    if arrayPivot == arrayLen: 
        s = tuple([sum(x)/arrayLen for x in zip(*circularArray)])
        sql.insertSensors(temp=s[0], humidity=s[1], carbon=s[4], acidity=s[2], saline=s[3], level=lvl)
        arrayPivot = 0

def mockArduino():
    global temp, ph, tds, co2, lvl

    while True:
        if not input_queue.empty():
            command_data = input_queue.get()
            print("Write data to serial " + command_data) #testing

        temp = round(random.uniform(20, 30), 2)
        ph = round(random.uniform(4, 10), 1)
        tds = round(random.uniform(500, 700))
        co2 = round(random.uniform(500, 1100))
        lvl = round(random.uniform(0.0, 1.0))
        insertSensorsIntoDB(temp, '0', ph, tds, co2, lvl)

        time.sleep(1)


def readArduino():
    global temp, hum, ph, tds, co2, lvl
    
    if not WINDOWS:
        arduino_path = auto_detect_serial()
        if arduino_path is not None:
            sp = serial_port.SerialPort(arduino_path)
        else:
            print("Arduino not connected")
            sys.exit(1)
    else:
        arduino_path = "COM8"
        sp = serial_port.SerialPort(arduino_path)

    print("Arduino path is", arduino_path) #testing
    sp.open()
    data = {"temp" : 0, "carb" : 0, "acid" : 0, "salin" : 0, "level" : 0}
    empty_loop_count = 0
    reconnect_count = 0
    first_data_pack_flag = False
    while True:
        try:
            if not input_queue.empty():
                command_data = input_queue.get()
                sp.write_serial(command_data.encode())
                print("Write data to serial " + command_data) #testing

            while sp.serial_available():
                empty_loop_count = 0
                data = json.loads(sp.read_serial())
                #print(data) #testing
                if not first_data_pack_flag:
                    reconnect_count = 0 
                    print("First package") #testing
                    current_time = datetime.fromtimestamp(data["time"])
                    print(current_time) #testing
                    set_systime(str(current_time))
                    first_data_pack_flag = True
            empty_loop_count += 1
            if empty_loop_count > 10:
                raise RuntimeError("Time is over")
        except (RuntimeError, OSError):
            sp.close()
            print("Serial port disconnect")
            print("Try to reconnect")
            reconnect_count += 1
            if reconnect_count > 3:
                print("Reconnection limit. Please restart your computer.")
                sys.exit(1)
            time.sleep(10) #testing
            arduino_path = auto_detect_serial()
            if arduino_path is not None:
                sp = serial_port.SerialPort(arduino_path)
            else:
                print("Arduino not connected")
                sys.exit(1)
            if sp.open():
                empty_loop_count = 0
                print("Connection succeful")
                input_queue.put(current_state)

        with lock:
            temp = data["temp"]
            ph = data["acid"]
            tds = data["salin"]
            co2 = data["carb"]
            lvl = data["level"]
            insertSensorsIntoDB(temp, '0', ph, tds, co2, lvl) #TODO need to remove hum

        time.sleep(1)

def auto_detect_serial():
    import glob
    path = glob.glob("/dev/ttyACM*")
    if len(path) > 0:
        return path[0]
    else:
        return None

def set_systime(datetime):
    os.system("sudo date --set='" + datetime + "'")

if __name__ == "__main__":

    sql.create()
    sql.createActivity()
    
    row = sql.selectActivity()
    current_state = Markup(row[0][0])
    input_queue.put(current_state)

    print("IS IT WINDOWS? -" + str(WINDOWS))
    print("SHOULD MOCK? -" + str(MOCK))

    lock = threading.Lock()
    if MOCK:
        getThread = threading.Thread(target=mockArduino)
    else:
        getThread = threading.Thread(target=readArduino)
    getThread.daemon = True
    getThread.start()

    def sigint_handler(signum, frame):
        print("Stop pressing the CTRL+C!")
        # need to fix
        sp.close()
        getThread.join()
        print("Join the thread. Is it alive?")
        print(getThread.is_alive())
        print("Exit application")
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()
        sys.exit(1)

    signal.signal(signal.SIGINT, sigint_handler)

    if DEBUG:
        app.run(host='0.0.0.0', debug=True, threaded=True)
    else:
        app.run(host='0.0.0.0', debug=False, threaded=True)
