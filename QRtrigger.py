import sys
import posix_ipc
import traceback
import time

image = sys.argv[1]
f = open("/var/tmp/qr.log","a")
try:
    mq = posix_ipc.MessageQueue("/motion_msg")
except:
    f.write(time.asctime() + traceback.format_exc())
else:
    mq.send(sys.argv[1])
    f.write(time.asctime() + traceback.format_exc())

