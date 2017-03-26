import iec

LF = '\x0a'
CR = '\x0d'
ACK = '\x06'
STX = '\x02'
SOH = '\x01'
ETX = '\x03'
EOT = '\x04'
NAK = '\x14'



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


class RepeatRequest():
    name = 'Repeat-request message'
    
    def msg(self):
        return NAK
    
    
class Request(Msg):
    name = 'request message'
    adr = ''                            # optional device address

    def msg(self):
        return '/?' + self.adr + '!' + CR + LF
    
    
class OptionSelect(Msg):
    name = 'option select message'
    '''
    v : protocol control character (in protocol mode C and E)
        0 - normal protocol procedure
        1 - secondary protocol procedure
        2 - HDLC protocol procedure
        3-9 - reserved for future applications
    
    z : Baud rate identification (for baud rate changeover)
        The request message, the identification message and the acknowledgement/option select
        message are transmitted at the initial rate of 300 Bd (except protocol mode D) The baud
        rate of the data message depends on the baud rate determined by the protocol
        a) protocol mode A (without baud rate changeover)
            Any desired printable characters except "/", "!" and as long as they are not specified for
            protocol mode B or protocol mode C
        b) Protocol mode B (with baud rate changeover, without acknowledgement/option select message)
            A - 600 Bd
            B - 1 200 Bd
            C - 2 400 Bd
            D - 4 800 Bd
            E - 9 600 Bd
            F - 19200Bd
            G, H, I - reserved for later extensions
        c) Protocol mode C and protocol mode E (with baud rate changeover, 
            with baud rate acknowledgement / option select message or other protocols)
            0 - 300 Bd
            1 - 600 Bd
            2 - 1 200 Bd
            3 - 2 400 Bd
            4 - 4 800 Bd
            5 - 9 600 Bd
            6 - 19 200 Bd
            7, 8, 9 - reserved for later extensions.
        d) Protocol mode D (data transmission at 2 400 Bd)
         Baud rate character is always 3.
    y : mode control character (in protocol modes C and E)
        0 - data readout
        1 - programming mode
        2 - binary mode (HDLC), see Annex E
        3-5 and A-Z - reserved for future applications
        6-9 - manufacturer-specific use
    '''
    def __init__(self, v, z, y):
        self.v = v  
        self.z = z
        self.y = y
    
    def msg(self):
        return ACK + self.v + self.z + self.y + CR + LF
    
    
class ProgCmd(Msg):
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
    
    def __init__(self, adr, data):
        self.adr = adr
        self.data = data
    
    def msg(self):
        s = SOH + self.c + self.d + STX + self.adr + '(' + self.data + ')' + ETX
        return s + self.bbc(s)
    
    
class ProgCmdPartialBlocks(ProgCmd):
    
    def msg(self):
        s = SOH + self.c + self.d + STX + self.adr + '(' + self.data + ')' + EOT
        return s + self.bbc(s)


class ProgCmdPwd(ProgCmd):
    name = ProgCmd.name + ' - password command'
    
    # d : command type identifier
    #    0 - data is operand for secure algorithm
    #    1 - data is operand for comparison with internally held password
    #    2 - data is result of secure algorithm (manufacturer-specific)
    #    3-9 - reserved for future use.
    def __init__(self, d, adr, data):
        self.__init__(adr, data)
        self.c = 'P'
        self.d = d


class ProgCmdRead(ProgCmd):
    name = ProgCmd.name + ' - read command'
    
    # command type identifier
    # 0 - reserved for future use
    # 1 - read ASCII-coded data
    # 2 - formatted communication coding method read (optional, see Annex C)
    # 3 - read ASCII-coded with partial block (optional)
    # 4 - formatted communication coding method read (optional, see Annex C)
    #     with partial block
    # 5,6 - reserved for national use
    # 7-9 - reserved for future use
    def __init__(self, d, adr, data):
        ProgCmd.__init__(adr, data)
        self.c = 'R'
        self.d = d


class ProgCmdR3(ProgCmdRead):
    name = ProgCmdRead.name + ', type 3'
    
    def __init__(self, adr, data):
        ProgCmdRead.__init__(self, '3', adr, data)
        

class ProgCmdR5(ProgCmd):
    name = ProgCmdRead.name + ', type 5'
    
    def __init__(self, adr, data):
        ProgCmdRead.__init__(self, '5', adr, data)
    
    
class Break(Msg):
    name = 'Break command'
    
    def msg(self):
        s = SOH + 'B0' + ETX
        return s + self.bbc(s)