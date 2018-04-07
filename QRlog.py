#!/usr/bin/python

import sqlite3
import datetime
import requests
import configparser

def line(mesg,token):
    line_notify_token = token
    line_notify_api = 'https://notify-api.line.me/api/notify'
    message = '\n' + mesg
    payload = {'message': message}
    headers = {'Authorization': 'Bearer ' + line_notify_token}
    line_notify = requests.post(line_notify_api, data=payload, headers=headers)

config = configparser.ConfigParser()
config.read('/home/pi/QRTimer/qrlog.ini')

dbname = config['QRlog']['dbname']
token = config['QRlog']['token']

conn = sqlite3.connect(dbname,
detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
cursor = conn.cursor()
sqlite3.dbapi2.converters['DATETIME'] = sqlite3.dbapi2.converters['TIMESTAMP']
cursor.execute(
    "CREATE TABLE IF NOT EXISTS qrtimer(datetime TEXT, name TEXT, duration INTEGER)")
cursor.execute(
      "CREATE INDEX IF NOT EXISTS text_datetime_idx on qrtimer(datetime)")

now = datetime.datetime.now()
last = now - datetime.timedelta(days=1)
cursor.execute('SELECT * FROM qrtimer where datetime > ?',(last,))
message = ""
for (d, name, duration) in  cursor.fetchall():
    message = message + d[5:16]+" " + str(duration) + "min " + name + "\n"
message = message[0:-1]
line(message,token)
conn.close()

