import serial
import time
import re
import sys
import msg



# COM settings

class COM_7E1_9600:
    port = ''
    baudrate = 9600
    bytesize = serial.SEVENBITS
    parity = serial.PARITY_EVEN
    stopbits = serial.STOPBITS_ONE

    def __init__(self, port=''):
        self.port = port



vserial0 = '/dev/tnt0'
vserial1 = '/dev/tnt1'


# AS3000 comunication

REQUEST = '/?!'                            # from client
IDENT = '\x06051'                          # from meter
ACK_OSM = '\x06051'                            # from client

PGR_CMD_MSG_1 = '\x01P0\x02(n..n)\x03m'    # from meter
PGR_CMD_MSG_2 = '\x01P2\x02(n..n)\x03e'    # from client
ACK = '\x06'                                   # from meter
R5 = '\x01R5\x02n..n()\x03\\'                   # from client
PM_DATA_MSG = 'adr(n..n)\x03\x1e'            # from meter

LFCR = '\r\n'


# AS3000 registers

TIME = '0.9.2'
PWR = '1.8.0'


PWD = '49036942'


DELAY = 1
WAIT = 1.5



        
        
class MeterDevice():
    
    def __init__(self, device):
        self.ser = serial.Serial(port=device.port,
                                 baudrate=device.baudrate,
                                 parity=device.parity,
                                 stopbits=device.stopbits,
                                 bytesize=device.bytesize)
        self.ser.isOpen()
        
        
    def show(self, s):
        mapping = [ (msg.LF, '<LF>'), 
                    (msg.CR, '<CR>'), 
                    ('\x06', '<ACK>'), 
                    ('\x01', '<SOH>'), 
                    ('\x02', '<STX>'), 
                    ('\x03', '<ETX>'),
                    ('\x04', '<EOT>')]
        for k, v in mapping:
            s = s.replace(k, v)
        print(s)
    
    def send_receive(self, msg, verbose=True, delay=DELAY):
        if verbose:
            self.show('send ' + msg.name)
            self.show('-> ' + msg.msg())
        self.ser.write(bytes(msg.msg(), 'utf-8'))
        
        
        print('waiting for incoming message..')
        slow_down = 200 / self.ser.baudrate
        out = ''
        t_start = time.time()
        nothing_received = True
        while time.time() - t_start < delay and nothing_received:
            while self.ser.inWaiting() > 0:
                out += str(self.ser.read(1))
                nothing_received = False
                time.sleep(slow_down)
        out = re.sub("[b']", "", out)
      
        if out:
            if verbose:
                self.show('..received:')
                self.show('<- ' + out)
            ret_value = out
        else:
            if verbose:
                self.show('..nothing received :(')
            ret_value = '-1'
        return ret_value
    


if __name__ == '__main__':

    AS3000 = COM_7E1_9600(port='/dev/ttyUSB0')
    meter = MeterDevice(AS3000)

    # send request message
    id_msg = meter.send_receive(msg.Request())
    if id_msg[:4] != '/ELS':
        print('..unknown device or comunication failed')
        meter.ser.close()
        sys.exit()
        
    # send ack / option select message
    meter.send_receive(msg.OptionSelect())



    # send exit command
    meter.send_receive(msg.Break())

    meter.ser.close()

