#!/usr/bin/python
import os
import sys
import RPi.GPIO as GPIO
import sqlite3
import re
import datetime, time, threading, posix_ipc
from pyzbar.pyzbar import decode
from PIL import Image

class ACOutlet():
  OUTLET = 11
  GREEN = 13
  RED = 15
  def __init__(self):
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)

    GPIO.setup(ACOutlet.OUTLET, GPIO.OUT)
    GPIO.setup(ACOutlet.GREEN, GPIO.OUT)
    GPIO.setup(ACOutlet.RED, GPIO.OUT)

    GPIO.output(ACOutlet.OUTLET, False)
    GPIO.output(ACOutlet.GREEN, False)
    GPIO.output(ACOutlet.RED, False)
    self._outlet_value = False
    self._green_value = False
    self._red_value = False
    self._blink_green = 0
    self._blink_red = 0

    self.owner = ""
    self.countdown = 0
    self.updatable = False
    self.hist = []
    self.today = ""

    self.dbname = '/var/log/motion/qrtimer.db'
    self.conn = sqlite3.connect(self.dbname,
                detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    sqlite3.dbapi2.converters['DATETIME'] = sqlite3.dbapi2.converters['TIMESTAMP']

    self.cursor = self.conn.cursor()
    self.cursor.execute(
      "CREATE TABLE IF NOT EXISTS qrtimer(datetime TEXT, name TEXT, duration INTEGER)")
    self.cursor.execute(
      "CREATE INDEX IF NOT EXISTS text_datetime_idx on qrtimer(datetime)")
    
    self.thread_led = threading.Thread(target = self.led)
    self.thread_led.start()

    self.thread_ACtimer = threading.Thread(target = self.ACtimer)
    self.thread_ACtimer.start()

  def dbinsert(self,owner,duration):
    self.cursor.execute("INSERT INTO qrtimer VALUES(?,?,?)",
                      (datetime.datetime.now(),owner,duration))
    self.conn.commit()

  def ACtimer(self):
    self.set_ACoutlet(False)
    self.set_Red(False)
    while True:
      if self.today != time.ctime()[:3]:
        self.hist = []
      self.today = time.ctime()[:3]
      if self.countdown > 0:
#        print "Owner:"+self.owner+" for "+str(self.countdown)+"\n"
#        print self.hist
        GPIO.output(ACOutlet.OUTLET,True)
        self.countdown -= 1
        if self.countdown < 10:
          self.blink_Red(60)
        else:
          self.set_Red(True)
        time.sleep(60)
      else:
        GPIO.output(ACOutlet.OUTLET,False)
        self.set_Red(False)
        time.sleep(5)
      
  def updateTimer(self, owner, counter, uflag):
    acoutlet.blink_Green(2)
    if uflag:
      self.owner = owner
      self.countdown = counter
      self.dbinsert(owner,counter)
 #     print "New owner(update):"+owner+" for"+str(counter)+"\n"
    else:
      if not (owner in self.hist):
        self.owner = owner
        self.countdown = counter
        self.dbinsert(owner,counter)
#        print "New owner(once):"+owner+" for"+str(counter)+"\n"
        self.hist.append(owner)
      
  def led(self):
    while True:
      GPIO.output(ACOutlet.GREEN, self._green_value)
      GPIO.output(ACOutlet.RED, self._red_value)
      if self._blink_green > 0:
        self._green_value = not self._green_value
        self._blink_green -= 1
      if self._blink_red > 0:
        self._red_value = not self._red_value
        self._blink_red -= 1
      time.sleep(1)

  def set_ACoutlet(self, val):
    self._outlet_value = val
    GPIO.output(ACOutlet.OUTLET, self._outlet_value)

  def set_Green(self, val):
    self._green_value = val
    self._blink_green = 0
    GPIO.output(ACOutlet.GREEN, self._outlet_value)

  def blink_Green(self, val):
    self._blink_green = val

  def set_Red(self,val):
    self._red_value = val
    self._blink_red = 0
    GPIO.output(ACOutlet.RED, self._red_value)

  def blink_Red(self, val):
    self._blink_red = val

if __name__ == '__main__':
  acoutlet = ACOutlet()
  last_decode = 0
  posix_ipc.unlink_message_queue("/motion_msg")
  mq = posix_ipc.MessageQueue("/motion_msg",posix_ipc.O_CREX)

  while True:
    filename, _ = mq.receive()
    if (time.time() - last_decode) > 15:
      data = decode(Image.open(filename))
      if data:
        m = re.match("(\w+)/(\w+)/(\d+)/(\w+)",
                data[0][0].decode('utf-8', 'ignore'))
        if m:
          (owner, day, minutes, flag) = m.groups()
          if flag == "TRUE":
            uflag = True
          else:
            uflag = False
          acoutlet.updateTimer(owner, int(minutes), uflag)
          last_decode =time.time()

    os.remove(filename)
