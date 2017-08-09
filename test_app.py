import sys
import iec
import msg
import time
from collections import deque

from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QWidget, QAction, QTabWidget,QVBoxLayout, QComboBox, QLabel
from PyQt5.QtWidgets import QHBoxLayout, QBoxLayout, QFormLayout, QGridLayout, QFrame, QGroupBox, QTextEdit, QStatusBar
from PyQt5.QtWidgets import QLabel, QLineEdit, QCheckBox
from PyQt5.QtCore import Qt, QMimeData, QThread, QObject, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5 import QtCore
import PyQt5



HELPSTRING_V = (
''' Protocol Control Character "V":
    0 - normal protocol procedure
    1 - secondary protocol procedure
    2 - HDLC protocol procedure''')

HELPSTRING_Z = (
''' Baud Rate Identification "Z":
    0 - 300 Bd
    1 - 600 Bd
    2 - 1200 Bd
    3 - 2400 Bd
    4 - 4800 Bd
    5 - 9600 Bd
    6 - 19200 Bd''')

HELPSTRING_Y = (
''' Mode Control Character "Y":
    0 - data readout
    1 - programming mode
    2 - binary mode (HDLC)''')

HELPSTRING_MSG_ID = (
''' Command Message Identifier
    P - Password command
    W - Write Command
    R - Read Command
    E - Execute Command
    B -  Exit Command (break)''')

HELPSTRING_TYPE_ID = (
''' Command type identifier (signifies the variant of the command)
    a) for password P command
        0 - data is operand for secure algorithm
        1 - data is operand for comparison with internally held password
        2 - data is result of secure algorithm (manufacturer-specific)

    b) for write W command
        0 - reserved for future use
        1 - write ASCII-coded data
        2 - formatted communication coding method write (optional)
        3 - write ASCII-coded with partial block (optional)
        4 - formatted communication coding method write with partial block (optional)

    c) for read R command
        0 - reserved for future use
        1 - read ASCII-coded data
        2 - formatted communication coding method read (optional)
        3 - read ASCII-coded with partial block (optional)
        4 - formatted communication coding method read with partial block (optional)
        5,6 - reserved for national use

    d) for execute E command
        0,1 - reserved for future use
        2 - formatted communication coding method execute (optional)

    e) for exit B command
        0 - complete sign-off
        1 - complete sign-off for battery operated devices using the fast wake-up method''')

HELPSTRING_DATA_SET = (
''' This provides the address and data for the message.
    "ID/Address ( [Value] [.Unit] )"
    The following applies to command messages:
    a) The password command P
        The address and unit fields are empty (devoid of any characters).
    b) The write command W
        Where the value represents a data string, the address is the start location
        to which the data is to be written. The unit field is left empty.
    c) The read command R
        Where a data string is to be read, the address is the start location from
        which data is read.
        The value represents the number of locations to be read including the start location.
        The unit field is left empty.
    d) The execute command E
        It requests that a device executes a predefined function.
    e) The exit command B
        No data set is required when the command type identifier is 0.''')


class ClickableLineEdit(QLineEdit):
    clicked = QtCore.pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self.clicked.emit()
        else: super().mousePressEvent(event)


class TextInput(QHBoxLayout):
    
    angryStyle = ('''
        QLineEdit {
            border-style: outset;
            border-width: 2px;
            border-color: red;
            }
        ''')
    
    def __init__(self, txt):
        super().__init__()
        self.label = QLabel(txt)
        self.input = ClickableLineEdit()
        self.input.clicked.connect(self.relax)
        self.input.textEdited.connect(self.relax)
        self.addWidget(self.label)
        self.addWidget(self.input)
        self.easyStyle = self.label.styleSheet()
    

    def setToolTip(self, s):
        self.label.setToolTip(s)
        self.input.setToolTip(s)
    
    def becomeAngry(self):
        self.input.setStyleSheet(self.angryStyle)
        
    def relax(self):
        self.input.setStyleSheet(self.easyStyle)
        
    def getValue(self):
        return self.input.text()


class ChooseSerialEventFilter(QObject):
    
    sig_update_serial_ports = pyqtSignal()
    
    def eventFilter(self, filteredObj, event):
        if event.type() == QtCore.QEvent.Show:
            print('serial combobox just clicked!')
            self.sig_update_serial_ports.emit()
        return QObject.eventFilter(self, filteredObj, event)
    
    
    
class MainView(QMainWindow):
    
    sig_data_changed = pyqtSignal()
    sig_run_queue = pyqtSignal()
    sig_req_msg = pyqtSignal(msg.Msg)

    def __init__(self):   
        super().__init__()
        
        self.setGeometry(300, 300, 580, 350)
        
        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()    
        self.tab2 = QWidget()
        self.tabs.resize(300,200) 
 
        # Add tabs
        self.tabs.addTab(self.tab1,"Settings")
        self.tabs.addTab(self.tab2,"Messages")
 
        # Create first tab
        self.tab1.layout = QFormLayout(self)
        
        # choose serial port
        self.chooseSerialLabel = QLabel()
        self.chooseSerialLabel.setText('Serial Port')
        self.chooseSerialCB = QComboBox()
        serialCBjustClicked = ChooseSerialEventFilter()
        self.chooseSerialCB.view().installEventFilter(serialCBjustClicked)
        self.chooseSerialCB.activated.connect(self.chooseSetting)
        
        # choose protocol
        self.chooseProtocolLabel = QLabel()
        self.chooseProtocolLabel.setText('Protocol')
        self.chooseProtocolCB = QComboBox()
        for protocol in iec.PROTOCOLS:
            self.chooseProtocolCB.addItem(protocol)
        self.chooseProtocolCB.activated.connect(self.chooseSetting)
        
        '''
        # choose start baudrate
        self.chooseStartBdLabel = QLabel()
        self.chooseStartBdLabel.setText('Start Baudrate')
        self.chooseStartBdCB = QComboBox()
        for bd in iec.BAUDRATES:
            self.chooseStartBdCB.addItem(str(bd))
        '''
        
        # choose baudrate
        self.chooseBaudrateLabel = QLabel()
        self.chooseBaudrateLabel.setText('Baudrate')
        self.chooseBaudrateCB = QComboBox()
        for bd in iec.BAUDRATES:
            self.chooseBaudrateCB.addItem(str(bd))
        self.chooseBaudrateCB.activated.connect(self.chooseSetting)
        
        self.tab1.layout.addRow(self.chooseSerialLabel,
                                     self.chooseSerialCB)
        self.tab1.layout.addRow(self.chooseProtocolLabel,
                                     self.chooseProtocolCB)
        #self.tab1.layout.addRow(self.chooseStartBdLabel,
        #                             self.chooseStartBdCB)
        self.tab1.layout.addRow(self.chooseBaudrateLabel,
                                     self.chooseBaudrateCB)
        self.tab1.setLayout(self.tab1.layout)
        
        # request msg button
        self.buttMsgRequest = QPushButton()
        self.buttMsgRequest.setText('Request Message')
        self.buttMsgRequest.clicked.connect(self.addRequestMsg)
        
        # request msg id input
        self.reqMsgIdInput = TextInput('Id (optional)')
        
        # request msg layout
        self.reqMsgLayout = QVBoxLayout()
        self.reqMsgLayout.addWidget(self.buttMsgRequest)
        self.reqMsgLayout.addLayout(self.reqMsgIdInput)
        
        # option select msg button
        self.buttMsgOptionSel = QPushButton()
        self.buttMsgOptionSel.setText('ACK/Option Select Message') 
        self.buttMsgOptionSel.clicked.connect(self.addOptionSelectMsg)
        
        # option select msg inputs
        self.osmVInput = TextInput('V')
        self.osmVInput.setToolTip(HELPSTRING_V)
        self.osmZInput = TextInput('Z')
        self.osmZInput.setToolTip(HELPSTRING_Z)
        self.osmYInput = TextInput('Y')
        self.osmYInput.setToolTip(HELPSTRING_Y)

        # option select msg layout
        self.osmLayout = QGridLayout()
        self.osmLayout.addWidget(self.buttMsgOptionSel, 1, 1, 1, 3)
        self.osmLayout.addLayout(self.osmVInput, 2, 1)
        self.osmLayout.addLayout(self.osmZInput, 2, 2)
        self.osmLayout.addLayout(self.osmYInput, 2, 3)
        
        # programming command message button
        self.buttProgCmdMsg = QPushButton()
        self.buttProgCmdMsg.setText('Programming Command Message')
        self.buttProgCmdMsg.clicked.connect(self.addProgCmdMsg)
        
        # programming command message inputs
        self.progCmdMsgIdInput = TextInput('Msg Id')
        self.progCmdMsgIdInput.setToolTip(HELPSTRING_MSG_ID)
        self.progCmdTypeIdInput = TextInput('Type Id')
        self.progCmdTypeIdInput.setToolTip(HELPSTRING_TYPE_ID)
        self.progCmdDataInput = TextInput('Data Set')
        self.progCmdDataInput.setToolTip(HELPSTRING_DATA_SET)
        
        # programming command message Layout
        self.progCmdLayout = QGridLayout()
        self.progCmdLayout.addWidget(self.buttProgCmdMsg, 1, 1, 1, 2)
        self.progCmdLayout.addLayout(self.progCmdMsgIdInput, 2, 1)
        self.progCmdLayout.addLayout(self.progCmdTypeIdInput, 2, 2)
        self.progCmdLayout.addLayout(self.progCmdDataInput, 3, 1, 3, 2)
        
        # messages layout
        self.msgLayout = QVBoxLayout()
        self.msgLayout.addLayout(self.reqMsgLayout)
        self.msgLayout.addLayout(self.osmLayout)
        self.msgLayout.addLayout(self.progCmdLayout)
        
        # messages frame
        self.msgFrame = QGroupBox()
        self.msgFrame.setTitle('Messages')
        self.msgFrame.setLayout(self.msgLayout)
        
        # data readout button
        self.buttDataReadout = QPushButton()
        self.buttDataReadout.setText('Data Readout')
        
        # register read button
        self.buttReadRegister = QPushButton()
        self.buttReadRegister.setText('Read Register')
        
        # jobs layout
        self.jobsLayout = QVBoxLayout()
        self.jobsLayout.addWidget(self.buttDataReadout)
        self.jobsLayout.addWidget(self.buttReadRegister)
        
        # jobs frame
        self.jobsFrame = QGroupBox()
        self.jobsFrame.setTitle('Jobs')
        self.jobsFrame.setLayout(self.jobsLayout)
        
        # queue text output
        self.queueText = QTextEdit()
        self.queueText.setReadOnly(True)
        
        # queue return button
        self.buttReturn = QPushButton()
        self.buttReturn.setText('Remove Last')
        
        # queue play/pause button
        self.buttPlay = QPushButton()
        self.buttPlay.setText('Play')
        self.buttPlay.clicked.connect(self.runQueue)
        
        # queue stop button
        self.buttStop = QPushButton()
        self.buttStop.setText('Clear')
        
        # queue forward button
        self.buttForward = QPushButton()
        self.buttForward.setText('Skip next')
                
        # queue layout
        self.queueLayout = QGridLayout()
        self.queueLayout.addWidget(self.queueText, 1, 1, 1, 4)
        self.queueLayout.addWidget(self.buttReturn, 2, 1)
        self.queueLayout.addWidget(self.buttPlay, 2, 2)
        self.queueLayout.addWidget(self.buttStop, 2, 3)
        self.queueLayout.addWidget(self.buttForward, 2, 4)
        
        # queue frame
        self.queueFrame = QGroupBox()
        self.queueFrame.setTitle('Queue')
        self.queueFrame.setLayout(self.queueLayout)
        
        # auto play checkbox
        self.autoPlay = QCheckBox('Auto Play')
        self.autoPlay.stateChanged.connect(self.autoPlayCheck)
        
        # auto break msg
        self.autoBreak = QCheckBox('Auto Break')
        
        # auto bd changeover
        self.autoBd = QCheckBox('Auto Bd Changeover')
        
        # options layout
        self.optionsLayout = QVBoxLayout()
        self.optionsLayout.addWidget(self.autoPlay)
        self.optionsLayout.addWidget(self.autoBreak)
        self.optionsLayout.addWidget(self.autoBd)
        
        # options frame
        self.optionsFrame = QGroupBox()
        self.optionsFrame.setTitle('Options')
        self.optionsFrame.setLayout(self.optionsLayout)
        
        
        self.tab2.layout = QGridLayout()
        self.tab2.layout.addWidget(self.msgFrame, 1, 1, 1, 2)
        self.tab2.layout.addWidget(self.jobsFrame, 1, 3, 1, 2)
        self.tab2.layout.addWidget(self.queueFrame, 2, 1, 1, 3)
        self.tab2.layout.addWidget(self.optionsFrame, 2, 4)
        self.tab2.setLayout(self.tab2.layout)
        
 
        # Add tabs   
        self.setCentralWidget(self.tabs)
        
        # set initial input data
        self.update_serial_ports()      
        
        
        
    def update_serial_ports(self):
        # update available serial ports
        self.chooseSerialCB.clear()
        for port in iec.serial_ports():
            self.chooseSerialCB.addItem(port)
        
    
    def chooseSetting(self):
        self.sig_data_changed.emit()
        
        
    def addRequestMsg(self):
        id = self.reqMsgIdInput.input.text()
        m = msg.Request()
        self.sig_req_msg.emit(m)
            
            
    def addOptionSelectMsg(self):
        # collect msg parameters
        v = self.osmVInput.getValue()
        z = self.osmZInput.getValue()
        y = self.osmYInput.getValue()
        # input fields are mandatory
        if not y:
            self.osmYInput.becomeAngry()
            self.osmYInput.input.setFocus()
        if not z:
            self.osmZInput.becomeAngry()
            self.osmZInput.input.setFocus()
        if not v:
            self.osmVInput.becomeAngry()
            self.osmVInput.input.setFocus()
        if all((y, z, v)):
            m = msg.OptionSelect(v, z, y)
            self.sig_req_msg.emit(m)


    def addProgCmdMsg(self):
        # collect msg parameters
        msg_id = self.progCmdMsgIdInput.getValue()
        type_id = self.progCmdTypeIdInput.getValue()
        data_set = self.progCmdDataInput.getValue()
        # input fields are mandatory
        if not data_set:
            self.progCmdDataInput.becomeAngry()
            self.progCmdDataInput.input.setFocus() 
        if not type_id:
            self.progCmdTypeIdInput.becomeAngry()
            self.progCmdTypeIdInput.input.setFocus()
        if not msg_id:
            self.progCmdMsgIdInput.becomeAngry()
            self.progCmdMsgIdInput.input.setFocus()
        if all((msg_id, type_id, data_set)):
            m = msg.ProgCmd(msg_id, type_id, data_set)
            self.sig_req_msg.emit(m)     
        
                
    def autoPlayCheck(self):
        if self.autoPlay.isChecked():
            self.runQueue()
            
            
    def runQueue(self):
        self.sig_run_queue.emit()
            
        
    def update(self, data):
        # update queue window
        self.queueText.clear()
        for msg in data['queue']:
            self.queueText.append(msg.name)
        
            
    def get_data(self):
        data  = dict()
        data['port'] = str(self.chooseSerialCB.currentText())
        data['baudrate'] = str(self.chooseBaudrateCB.currentText())
        data['protocol'] = str(self.chooseProtocolCB.currentText())
        data['autobreak'] = self.autoBreak.isChecked()
        data['autoplay'] = self.autoPlay.isChecked()
        return data



class ComView(QMainWindow):
    
    def __init__(self, auto_close=True):
        super().__init__()
        self.auto_close = auto_close
        self.setGeometry(100, 100, 580, 350)
        
        self.comLog = QTextEdit(self)
        self.comLog.setReadOnly(True)
        
        self.layout = QGridLayout()
        self.layout.addWidget(self.comLog,1,1,1,1)
        
        self.widget = QWidget()
        self.widget.layout = self.layout
        
        self.centralwidget = self.widget
        self.setWindowTitle('Communication Log')

        
    def log(self, s):
        self.comLog.add

    def update(self, data):
        pass
    
    def get_data(self):
        return dict()


class IecApp(QObject):

    sig_abort_com = pyqtSignal()
    sig_update_views = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.state = 'no_serial'
        self.meter = None
        self.queue = []
        self.comunicating = False
        self.data = dict()
        self.data['queue'] = self.queue
        
        self.mainView = MainView()
        self.comView = ComView()
        self.views = {self.mainView, self.comView}
        
        for view in self.views:
            self.sig_update_views.connect(view.update)
        
        self.mainView.sig_data_changed.connect(self.collect_data_from_gui)
        self.mainView.buttPlay.clicked.connect(self.run_queue)
        self.mainView.sig_req_msg.connect(self.addRequestMsg)
        
        self.updateViews()
        self.mainView.show()
        
        self.ui_data = dict()
        self.collect_data_from_gui()
        


    def updateViews(self):
        self.sig_update_views.emit(self.data)
        gui.processEvents()
    
    
    def collect_data_from_gui(self):
        for view in self.views:
            self.ui_data.update(view.get_data())

    
    def addRequestMsg(self, m):
        self.queue.append(m)
        self.updateViews()
            
            
    def run_queue(self):
        if self.queue and not self.comunicating:
            # show communication view
            self.comView.show()
            
            # start comunication in different thread
            self.comunicating = True
            self.serialCom = SerialCom(self.queue[0], self.ui_data)
            self.serialThread = QThread()
            self.serialCom.moveToThread(self.serialThread)
            
            self.serialCom.sig_com_done.connect(self.com_done)
            #self.sig_abort_com.connect(self.serialCom.abort)
            
            self.serialThread.started.connect(self.serialCom.run)
            self.serialThread.start()
            
            self.updateViews()
            
    
    @pyqtSlot()
    def com_done(self):
        # abort thread
        #self.sig_abort_com.emit()
        self.serialThread.quit()
        self.serialThread.wait()
        self.comunicating = False
        
        # update queue
        if self.queue:
            self.queue.pop(0)
            
        self.updateViews()
        
        if self.queue:
            self.run_queue()
             
     
     
class SerialCom(QObject):
    
    sig_com_done = pyqtSignal()
    sig_com_log = pyqtSignal(object)
    sig_state = pyqtSignal(object)
    
    def __init__(self, job, com_settings, logView=None):
        super().__init__()
        self.job = job
        self.com = com_settings
        self.logView = logView
    
    
    def attach_meter(self):
        if self.com['port']:
            self.meter = iec.IecDevice(self.com['port'], verbose=True)
            self.meter.baudrate = self.com['baudrate']
            self.meter.protocol = self.com['protocol']
            self.meter.sig_received_data.connect(self.received_data)
            self.meter.sig_state.connect(self.state_changed)
        else:
            self.meter = None
    
    
    def detach_meter(self):
        self.meter.ser.close()
        self.meter = None
    
    
    @pyqtSlot() 
    def run(self):
        self.attach_meter()
        self.meter.send_receive(self.job)    
        self.detach_meter()
        self.sig_com_done.emit()
           
           
    def received_data(self, data):
        self.sig_com_log.emit(data)
    
    def state_changed(self, msg):
        self.sig_state.emit(msg)
               
    def abort(self):
        self.__abort = True
    
      
if __name__ == '__main__':
  
    gui = QApplication(sys.argv)
    controller = IecApp()
    
    
    gui.exec_()  