import iec_com

meter = iec_com.IecDev(iec_com.COM_7E1_9600(port='COM7'))
meter.send_msg(iec_com.ProgCmdMsgExit())