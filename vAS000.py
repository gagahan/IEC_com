from iec_com import *
import time
    
    
ID_MSG = '/ELS5@V10.04' + CR + LF

ser = None

def receive():
    rev = bytes()
    while ser.inWaiting() > 0:
        rev += ser.read(1)
        time.sleep(0.1)
    if rev:
        #print(rev)
        #rev = re.sub("[b']", "", rev)
        print('reveived: ', rev)
    return rev

def transmit(s, delay=0.005):
    time.sleep(delay)
    print('transmit:', s)
    for c in s:
        ser.write(bytes(c, 'utf-8'))
        time.sleep(delay)
        


if __name__ == '__main__':
    
    ser = vserial1
    
    while True:
        rev = receive()
        
        if rev == bytes(RequestMsg().msg(), 'utf-8'):
            transmit(ID_MSG)
        
        