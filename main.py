import time
import serial
import re


# configure the serial connections (the parameters differs on the device you are connecting to)
'''
P5S = serial.Serial(
    port='COM5',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS
)

AS3000 = serial.Serial(
    port='COM4',
    baudrate=9600,
    parity=serial.PARITY_EVEN,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.SEVENBITS
)
'''

vserial0= serial.Serial(
    port='/dev/tnt0',
    baudrate=9600,
    parity=serial.PARITY_EVEN,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.SEVENBITS
)

vserial1 = serial.Serial(
    port='/dev/tnt1',
    baudrate=9600,
    parity=serial.PARITY_EVEN,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.SEVENBITS
)

def map_str(s):
    mapping = [ ('\x0a', '<LF>'), 
               ('\x0d', '<CR>'), 
               ('\x06', '<ACK>'), 
               ('\x01', '<SOH>'), 
               ('\x02', '<STX>'), 
               ('\x03', '<ETX>'),
               ('\x04', '<EOT>') ]
    for k, v in mapping:
        s = s.replace(v, k)
    return s




ser = P5S

ser.isOpen()
print('Enter your commands below.\r\nInsert "exit" to leave the application.')

eingabe=1
while 1 :
    # get keyboard input
    eingabe = input(">> ")
    if eingabe == 'exit':
        ser.close()
        exit()
    else:
        # send the character to the device
        # (note that I happend a \r\n carriage return and line feed to the characters - this is requested by my device)
        eingabe = map_str(eingabe)
        b = bytes(eingabe, 'utf-8')
        ser.write(b)
        out = ''
        # let's wait one second before reading output (let's give device time to answer)
        time.sleep(1)
        while ser.inWaiting() > 0:
            out += str(ser.read(1))

        if out != '':
            print(">>" + re.sub("[b']", "", out))
            