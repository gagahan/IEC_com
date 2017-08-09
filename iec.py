import serial
import time
import re
import sys
import msg
import glob
from posix import device_encoding
from PyQt5.QtCore import pyqtSignal, QObject




# constants
_7E1 = '7E1'
_8N1 = '8N1'

NORMAL_PROTOCOL_PROCEDURE = '0'
SECONDARY_PROTOCOL_PROCEDURE = '1'
HDLC_PROTOCOL_PROCEDURE = '2'
_300BAUD = '0'
_600BAUD = '1'
_1200BAUD = '2'
_2400BAUD = '3'
_4800BAUD = '4'
_9600BAUD = '5'
_19200BAUD = '6'
DATA_READOUT = '0'
PROGRAMMING_MODE = '1'
BINARY_MODE = '2'


PROTOCOLS = ('7E1', '8N1')
BAUDRATES = (300, 600, 1200, 2400, 4800, 9600, 19200)


vserial0 = '/dev/tnt0'
vserial1 = '/dev/tnt1'

# list serial ports
def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
        ports += glob.glob('/dev/tnt*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result




# AS3000 comunication
'''
REQUEST = '/?!'                            # from client
IDENT = '\x06051'                          # from meter
ACK_OSM = '\x06051'                            # from client

PGR_CMD_MSG_1 = '\x01P0\x02(n..n)\x03m'    # from meter
PGR_CMD_MSG_2 = '\x01P2\x02(n..n)\x03e'    # from client
ACK = '\x06'                                   # from meter
R5 = '\x01R5\x02n..n()\x03\\'                   # from client
PM_DATA_MSG = 'adr(n..n)\x03\x1e'            # from meter

LFCR = '\r\n'

'''
# AS3000 registers

        
        
class IecDevice(QObject):
    
    STATES = ('idle', 'sending', 'waiting', 'receiving')

    sig_state = pyqtSignal(object)
    sig_received_data = pyqtSignal(object)
    
    def __init__(self, port, protocol='7E1', bdr=9600, verbose=False):
        
        super().__init__()
        self.verbose = verbose
        
        # init serial port

        self.port = port
        self.setBaudrate(bdr)
        self.setProtocol(protocol)        
        if verbose:
            print('init serial port: ', 
                  self.port, self.baudrate, self.protocol)
        self.ser = serial.Serial(port=self.port,
                                 baudrate=self.baudrate)
        self.setTimeOut(1.5)
        self.setState('idle')
        self.slow_down = 300
    
    
    def setTimeOut(self, t):
        self.timeout = t;
    
    def setState(self, state):
        if state in self.STATES:
            self.state = state;
            
    def setProtocol(self, protocol):
        if protocol in PROTOCOLS:
            self.protocol = protocol
        
    def setBaudrate(self, bdr):
        if bdr in BAUDRATES:
            self.baudrate = bdr
        
        
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
        return(s)
    
    def baudrate_changeover(self, bd):
        mapping = [ (_300BAUD, 300),
                    (_600BAUD, 600),
                    (_1200BAUD, 1200),
                    (_2400BAUD, 2400),
                    (_4800BAUD, 4800),
                    (_9600BAUD, 9600),
                    (_19200BAUD, 19200)]
    
        for k, v in mapping:
            if bd == k:
                if self.verbose:
                    print('set baudrate to', v)
                self.ser.baudrate = v
                return v
    
    def send(self, msg):
        self.sig_state.emit('sending ' + msg.name)
        if self.verbose:
            print('send ' + msg.name)
            print('-> ' + self.show(str(msg.msg())))
        return self.ser.write(bytes(msg.msg(), 'utf-8'))
    
    
    def receive(self, msg_end=''):
        msg_end = bytes(msg_end, 'utf-8')
        self.sig_state.emit('waiting for incoming message..')
        if self.verbose:
            print('waiting for incoming message..')
        slow_down = self.slow_down / self.ser.baudrate
        out = bytes()
        t_start = time.time()
        nothing_received = True
        while time.time() - t_start < self.timeout and nothing_received:
            while self.ser.inWaiting() > 0:
                out += self.ser.read(1)
                nothing_received = False
                if msg_end:
                    l = len(msg_end)
                    if out[-l:] == msg_end:
                        yield re.sub("[b']", "", str(out))
                        out = bytes()
                time.sleep(slow_down/2)
        #out = re.sub("[b']", "", str(out))
      
        if out:
            sig_received_data.emit(out)
            if self.verbose:
                self.show('..received:')
                self.show('<- ' + str(bytes(out, 'utf-8')))
            ret_value = out
        else:
            if self.verbose:
                self.show('..nothing received :(')
            ret_value = '-1'
        yield ret_value
    
    
    def easy_receive(self):
        if self.verbose:
            print('receive message..')
        out = bytes()
        while self.ser.inWaiting() > 0:
            out += self.ser.read(1)
            print('.', end='', flush=True)
            time.sleep(.05)
        if out:
            print()
        if self.verbose:
                print('..received:')
                print(self.show('<- ' + str(out, 'utf-8')))
        return out   
    
    def send_receive(self, msg):
        self.send(msg)
        for data in self.receive():
            return data
        print('end')
    
    def wait_for_input(self):
        print('wait for input')
        while self.ser.inWaiting() == 0:
            pass
    


if __name__ == '__main__':


    serial_ports()
    #meter = IecDevice(COM_7E1_300(port='/dev/ttyUSB0'), verbose=True)
    '''
    # send request message
    id_msg = meter.send_receive(msg.Request())
    if id_msg[:4] != '/ELS':
        print('..unknown device or comunication failed')
        meter.send(msg.Break())
        meter.ser.close()
        sys.exit()
    else:
        device_baudrate = id_msg[4]
    # send ack / option select message
    meter.send(msg.OptionSelect(NORMAL_PROTOCOL_PROCEDURE,
                                device_baudrate,
                                PROGRAMMING_MODE ))
    
    meter.baudrate_changeover(device_baudrate)
    
    

    

    for i, data in enumerate(meter.receive(msg_end=msg.CR + msg.LF)):
        print(data)
        if i == 10:
            break
    '''
   # meter
    #meter.send_receive(msg.ProgCmdR5(adr='0.9.6',data=''))
    


