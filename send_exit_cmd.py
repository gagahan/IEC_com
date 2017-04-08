import iec
import msg

meter = iec.IecDevice(iec.COM_7E1_9600(port='/dev/ttyUSB0'), verbose=True)
meter.send(msg.Break())

meter.ser.close()