import iec
import msg

meter = iec.MeterDevice(iec.COM_7E1_9600(port='/dev/ttyUSB0'))
meter.send_msg(msg.Break())