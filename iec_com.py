import serial
import time
import re
import sys


LF = '\x0a'
CR = '\x0d'
ACK = '\x06'
STX = '\x02'
SOH = '\x01'
ETX = '\x03'
EOT = '\x04'

# COM settings

AS3000 = serial.Serial(
    port='COM4',
    baudrate=9600,
    parity=serial.PARITY_EVEN,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.SEVENBITS
)


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


class Msg():
    
    def bbc(self, s):
        buffer = bytes(s, 'utf-8')
        bcc = 1
        for byte in buffer:
            bcc ^= byte
        return chr(bcc)


class AckMsg():
    name = 'ACK message'
    
    def msg(self):
        return ACK


class RequestMsg(Msg):
    name = 'request message'
    adr = ''                            # optional device address

    def msg(self):
        return '/?' + self.adr + '!' + CR + LF
    
    
class OptionSelectMsg(Msg):
    name = 'option select message'
    v = '0'                             # protocol character
    z = '5'                             # baud rate identification
    y = '1'                             # mode control character
    
    def msg(self):
        return ACK + self.v + self.z + self.y + CR + LF
    
    
class ProgCmdMsg(Msg):
    name = 'programming command message'
    
    c = ''                              # command message identifier
                                        # 'P' : password command
                                        # 'W' : write command
                                        # 'R' : read command
                                        # 'E' : execute command
                                        # 'B' : exit command
                                        
    d = ''                              # command type identifier
    
    adr = ''                            # address
    data = ''                           # data set
    
    def __init__(self, adr='', data=''):
        self.adr = adr
        self.data = data
    
    def msg(self):
        s = SOH + self.c + self.d + STX + self.adr + '(' + self.data + ')' + ETX
        return s + self.bbc(s)


class ProgCmdMsgR5(ProgCmdMsg):
    name = ProgCmdMsg.name + ' - read command'
    c = 'R'                             # read command
    
    d = '5'                             # command type identifier
                                        # 0 - reserved for future use
                                        # 1 - read ASCII-coded data
                                        # 2 - formatted communication coding method read (optional, see Annex C)
                                        # 3 - read ASCII-coded with partial block (optional)
                                        # 4 - formatted communication coding method read (optional, see Annex C)
                                        #     with partial block
                                        # 5,6 - reserved for national use
                                        # 7-9 - reserved for future use


class ProgCmdMsgR3(ProgCmdMsg):
    name = ProgCmdMsg.name + ' - read command'
    c = 'R'                             # read command
    
    d = '3'                             # command type identifier
                                        # 0 - reserved for future use
                                        # 1 - read ASCII-coded data
                                        # 2 - formatted communication coding method read (optional, see Annex C)
                                        # 3 - read ASCII-coded with partial block (optional)
                                        # 4 - formatted communication coding method read (optional, see Annex C)
                                        #     with partial block
                                        # 5,6 - reserved for national use
                                        # 7-9 - reserved for future use
        

class ProgCmdMsgPwd(ProgCmdMsg):
    name = ProgCmdMsg.name + ' - password command'
    c = 'P'                             # pwd command
    
    d = '2'
    
    
class ProgCmdMsgExit(ProgCmdMsg):
    name = ProgCmdMsg.name + ' - exit command'
    
    def msg(self):
        s = SOH + 'B0' + ETX
        return s + self.bbc(s)
        
        
class IecDev():
    
    def __init__(self, serial):
        self.ser = AS3000
        self.ser.isOpen()
        
    def show(self, s):
        mapping = [ (LF, '<LF>'), 
                    (CR, '<CR>'), 
                    ('\x06', '<ACK>'), 
                    ('\x01', '<SOH>'), 
                    ('\x02', '<STX>'), 
                    ('\x03', '<ETX>'),
                    ('\x04', '<EOT>')]
        for k, v in mapping:
            s = s.replace(k, v)
        print(s)
    
    def send_msg(self, msg, verbose=True, delay=DELAY):
        if verbose:
            self.show('send ' + msg.name)
            self.show('-> ' + msg.msg())
        self.ser.write(bytes(msg.msg(), 'utf-8'))
        
        slow_down = 100 / self.ser.baudrate
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

    meter = IecDev(AS3000)

    # send request message
    id_msg = meter.send_msg(RequestMsg())
    if id_msg[:4] != '/ELS':
        print('..unknown device or comunication failed')
        meter.ser.close()
        sys.exit()
        
    # send ack / option select message
    meter.send_msg(OptionSelectMsg())

    #send P2 command
    meter.send_msg(ProgCmdMsgPwd(data=PWD))

    # send R3 command
    meter.send_msg(ProgCmdMsgR3(adr='C01000000000'))
    meter.send_msg(AckMsg())



    # send exit command
    meter.send_msg(ProgCmdMsgExit())

    meter.ser.close()

