import iec_com

meter = iec_com.IecDev(iec_com.AS3000)
meter.send_msg(iec_com.ProgCmdMsgExit())