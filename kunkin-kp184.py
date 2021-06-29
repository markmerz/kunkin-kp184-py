#!/usr/bin/python3

# udevadm info -q path -n /dev/ttyUSB1
MY_DEVICE = "/devices/pci0000:00/0000:00:14.0/usb3/3-3/3-3.4/3-3.4.4/3-3.4.4:1.0/"

from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from pymodbus.payload import BinaryPayloadBuilder, BinaryPayloadDecoder
from pymodbus.constants import Endian
import math
import glob
import subprocess
import sys

def main():
    mode_seen = False
    requested_mode = None
    dcload = Kunkin_KP184()

    if len(sys.argv) < 2:
        print_help_and_exit()
    for param in sys.argv[1:]:
        if mode_seen == True:            
            mode_value = float(param.replace(',', '.'))
            if requested_mode == "CV":
                dcload.set_CV_setting(mode_value)
                print("Configured Constant Voltage is {} V".format(dcload.get_CV_setting()))
            elif requested_mode == "CC":
                dcload.set_CC_setting(mode_value)
                print("Configured Constant Current is {} A".format(dcload.get_CC_setting()))
            elif requested_mode == "CW":
                dcload.set_CW_setting(mode_value)
                print("Configured Constant Power is {} W".format(dcload.get_CW_setting()))
            elif requested_mode == "CR":
                dcload.set_CR_setting(mode_value)
                print("Configured Constant Resistance is {} Ω".format(dcload.get_CR_setting()))
            mode_seen = False
            requested_mode = None

        elif param == "status":
            loadstatus = dcload.get_load_onoff()
            print("Load is {}".format(loadstatus))
            print("Measured Voltage is {} V".format(dcload.get_U_measure()))
            if loadstatus == "ON":                
                print("Measured Current is {} A".format(dcload.get_I_measure()))
                print("Measured Power is {} W".format(dcload.get_P_measure()))
                print("Measured Resistance is {} Ω".format(dcload.get_R_measure()))
            workmode = dcload.get_load_mode()
            print("Work mode is {}".format(workmode))
            if workmode == "CV":
                print("Configured Constant Voltage is {} V".format(dcload.get_CV_setting()))
            elif workmode == "CC":
                print("Configured Constant Current is {} A".format(dcload.get_CC_setting()))
            elif workmode == "CW":
                print("Configured Constant Power is {} W".format(dcload.get_CW_setting()))
            elif workmode == "CC":
                print("Configured Constant Resistance is {} Ω".format(dcload.get_CR_setting()))
            
        elif param == "on":
            dcload.set_load_onoff("ON")
            loadstatus = dcload.get_load_onoff()
            print("Load is {}".format(loadstatus))            

        elif param == "off":            
            dcload.set_load_onoff("OFF")
            loadstatus = dcload.get_load_onoff()
            print("Load is {}".format(loadstatus))

        elif param == "cv":
            mode_seen = True
            requested_mode = "CV"
            load_mode = dcload.get_load_mode()
            if load_mode != "CV":                
                loadstatus = dcload.get_load_onoff()
                if loadstatus != "OFF":
                    print("Work Mode change: switching load off")
                    dcload.set_load_onoff("OFF")
                    loadstatus = dcload.get_load_onoff()
                    print("Load is {}".format(loadstatus))
                    
                dcload.set_load_mode("CV")
                workmode = dcload.get_load_mode()
                print("Work mode is {}".format(workmode))

        elif param == "cc":
            mode_seen = True
            requested_mode = "CC"
            load_mode = dcload.get_load_mode()
            if load_mode != "CC":                
                loadstatus = dcload.get_load_onoff()
                if loadstatus != "OFF":
                    print("Work Mode change: switching load off")
                    dcload.set_load_onoff("OFF")
                    loadstatus = dcload.get_load_onoff()
                    print("Load is {}".format(loadstatus))
                
                dcload.set_load_mode("CC")
                workmode = dcload.get_load_mode()
                print("Work mode is {}".format(workmode))

        elif param in ["cw", "cp"]:
            mode_seen = True
            requested_mode = "CW"
            load_mode = dcload.get_load_mode()
            if load_mode != "CW":                
                loadstatus = dcload.get_load_onoff()
                if loadstatus != "OFF":
                    print("Work Mode change: switching load off")
                    dcload.set_load_onoff("OFF")
                    loadstatus = dcload.get_load_onoff()
                    print("Load is {}".format(loadstatus))
                
                dcload.set_load_mode("CW")
                workmode = dcload.get_load_mode()
                print("Work mode is {}".format(workmode))

        elif param == "cr":
            mode_seen = True
            requested_mode = "CR"
            load_mode = dcload.get_load_mode()
            if load_mode != "CR":                
                loadstatus = dcload.get_load_onoff()
                if loadstatus != "OFF":
                    print("Work Mode change: switching load off")
                    dcload.set_load_onoff("OFF")
                    loadstatus = dcload.get_load_onoff()
                    print("Load is {}".format(loadstatus))
                
                dcload.set_load_mode("CR")
                workmode = dcload.get_load_mode()
                print("Work mode is {}".format(workmode))
        else:
            print_help_and_exit()            

def print_help_and_exit():
    print(
            """Usage: kunkin-kp184.py status
Usage: kunkin-kp184.py on
Usage: kunkin-kp184.py off
Usage: kunkin-kp184.py cc 0.1
Usage: kunkin-kp184.py cv 0.2
Usage: kunkin-kp184.py cr 200
Usage: kunkin-kp184.py cv 0.3
Usage: kunkin-kp184.py cc 0.5 on status"""
            , file=sys.stderr)
    sys.exit(1)    

class Kunkin_KP184:
    client = None
    UNIT = 0x1
    LOAD_ONOFF = ["OFF", "ON"]
    LOAD_MODE = ["CV", "CC", "CR", "CW"]

    def __init__(self):
        for dev_hook in glob.iglob("/dev/ttyUSB*"):
            result = subprocess.run(["udevadm", "info", "-q", "path", "-n", dev_hook], stdout=subprocess.PIPE)
            res = result.stdout.decode('utf-8').strip()
            if res.startswith(MY_DEVICE):
                self.client = ModbusClient(method="rtu", port=dev_hook, timeout=0.2, baudrate=9600, stopbits=1, bytesize=8, parity="N")
                break
        else:
            raise ValueError("Serial port or adapter was not found at {}".format(MY_DEVICE))

    def __del__(self):
        if self is not None:
            if self.client is not None:
                self.client.close()

    def get_U_measure(self):
        rr = self.client.read_holding_registers(0x0122, count=4, unit=self.UNIT)
        if rr.isError():
            raise ValueError(rr)
        decoder = BinaryPayloadDecoder.fromRegisters(rr.registers, wordorder=Endian.Big, byteorder=Endian.Big)
        voltage = decoder.decode_32bit_uint() / 1000
        return voltage

    def get_I_measure(self):
        rr = self.client.read_holding_registers(0x0126, count=4, unit=self.UNIT)
        if rr.isError():
            raise ValueError(rr)
        decoder = BinaryPayloadDecoder.fromRegisters(rr.registers, wordorder=Endian.Big, byteorder=Endian.Big)
        amperage = decoder.decode_32bit_uint() / 1000
        return amperage

    def get_P_measure(self):
        return round(self.get_U_measure() * self.get_I_measure(), 2)

    def get_R_measure(self):
        try: 
            return round(self.get_U_measure() / self.get_I_measure(), 2)
        except ZeroDivisionError:
            return math.inf

    def get_load_mode(self):
        rr = self.client.read_holding_registers(0x0110, count=4, unit=self.UNIT)
        if rr.isError():
            raise ValueError(rr)
        decoder = BinaryPayloadDecoder.fromRegisters(rr.registers, wordorder=Endian.Big, byteorder=Endian.Big)
        res = decoder.decode_32bit_uint()
        return self.LOAD_MODE[res & 0xFF]

    def set_load_mode(self, load_mode):
        mode = self.LOAD_MODE.index(load_mode)

        builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Big)
        builder.add_32bit_uint(mode)
        payload = builder.build()
        tosend = bytearray(b'\x00\x01\x04')
        for c in payload:
            tosend.extend(c)
        rq = self.client.write_register(0x0110, tosend, skip_encode=True, unit=self.UNIT)

    def get_load_onoff(self):
        rr = self.client.read_holding_registers(0x010E, count=4, unit=self.UNIT)
        if rr.isError():
            raise ValueError(rr)
        decoder = BinaryPayloadDecoder.fromRegisters(rr.registers, wordorder=Endian.Big, byteorder=Endian.Big)
        res = decoder.decode_32bit_uint()
        return self.LOAD_ONOFF[res & 0xFF]

    def set_load_onoff(self, status):
        status = str(status)

        builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Big)

        if status in ["0", "off", "OFF"]:            
            builder.add_32bit_uint(0)      
        elif status in ["1", "on", "ON"]:
            builder.add_32bit_uint(1)
        else:
            raise ValueError("set_load_onoff(0 | off | OFF | 1 | on | ON)")

        payload = builder.build()
        tosend = bytearray(b'\x00\x01\x04')
        for c in payload:
            tosend.extend(c)
        rq = self.client.write_register(0x010E, tosend, skip_encode=True, unit=self.UNIT)        

    def get_CV_setting(self):
        rr = self.client.read_holding_registers(0x0112, count=4, unit=self.UNIT)
        if rr.isError():
            raise ValueError(rr)
        decoder = BinaryPayloadDecoder.fromRegisters(rr.registers, wordorder=Endian.Big, byteorder=Endian.Big)
        voltage = decoder.decode_32bit_uint() / 1000        
        return voltage

    def set_CV_setting(self, voltage):
        builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Big)
        builder.add_32bit_uint(int(round(voltage * 1000, 0)))
        payload = builder.build()
        tosend = bytearray(b'\x00\x01\x04')
        for c in payload:
            tosend.extend(c)
        rq = self.client.write_register(0x0112, tosend, skip_encode=True, unit=self.UNIT)

    def get_CC_setting(self):
        rr = self.client.read_holding_registers(0x0116, count=4, unit=self.UNIT)
        if rr.isError():
            raise ValueError(rr)
        decoder = BinaryPayloadDecoder.fromRegisters(rr.registers, wordorder=Endian.Big, byteorder=Endian.Big)
        amperage = decoder.decode_32bit_uint() / 1000
        return amperage

    def set_CC_setting(self, amperage):
        builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Big)
        builder.add_32bit_uint(int(round(amperage * 1000, 0)))
        payload = builder.build()
        tosend = bytearray(b'\x00\x01\x04')
        for c in payload:
            tosend.extend(c)
        rq = self.client.write_register(0x0116, tosend, skip_encode=True, unit=self.UNIT)        
    
    def get_CR_setting(self):
        rr = self.client.read_holding_registers(0x011A, count=4, unit=self.UNIT)
        if rr.isError():
            raise ValueError(rr)
        decoder = BinaryPayloadDecoder.fromRegisters(rr.registers, wordorder=Endian.Big, byteorder=Endian.Big)
        resistance = decoder.decode_32bit_uint() / 10
        return resistance

    def set_CR_setting(self, resistance):
        builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Big)
        builder.add_32bit_uint(int(round(resistance * 10, 0)))
        payload = builder.build()
        tosend = bytearray(b'\x00\x01\x04')
        for c in payload:
            tosend.extend(c)
        rq = self.client.write_register(0x011A, tosend, skip_encode=True, unit=self.UNIT)

    def get_CW_setting(self):
        rr = self.client.read_holding_registers(0x011E, count=4, unit=self.UNIT)
        if rr.isError():
            raise ValueError(rr)
        decoder = BinaryPayloadDecoder.fromRegisters(rr.registers, wordorder=Endian.Big, byteorder=Endian.Big)
        power = decoder.decode_32bit_uint() / 100
        return power

    def set_CW_setting(self, power):
        builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Big)
        builder.add_32bit_uint(int(round(power * 100, 0)))
        payload = builder.build()
        tosend = bytearray(b'\x00\x01\x04')
        for c in payload:
            tosend.extend(c)
        rq = self.client.write_register(0x011E, tosend, skip_encode=True, unit=self.UNIT)

if __name__ == "__main__":
    main()
