"""
Designed to rely upon a config file for initial setup
"""


import serial
import serial.tools.list_ports
from threading import Lock, Thread, Event
from time import sleep

from logs.logger import log_error
from config import Config
from config.meter_enum import MeterEnum


class Meter:
    """Meter class for generic BK Precision 5491B/5492B connections.
    Parameters can be modified from within config.config.json"""

    def __init__(self, dev: MeterEnum, callback):
        cfg: Config = Config.get_instance()
        self.Baud = cfg.meterBAUD
        self.Dev = dev
        if dev.value:
            self.Com = cfg.dutCOM
            self.serial_num = cfg.dut_serial_num
            self.Model = cfg.dut_model
        else:
            self.Com = cfg.refCOM
            self.serial_num = cfg.ref_serial_num
            self.Model = cfg.ref_model
        self.Port = serial.Serial(port=None, baudrate=self.Baud, timeout=1)
        self.Thread = Thread(target=self.read, args=())
        self.Lock = Lock()
        self.Callback = callback
        self.Should_Read = True
        self.GotReading = Event()

    def connect(self):
        """Search for Meter.
        Raise RuntimeError if unable to find properly configured device"""
        cfg: Config = Config.get_instance()
        if self.Com == "":
            self.Com = self.find_meter_comport()
        try:
            port = serial.Serial(port=self.Com, baudrate=self.Baud, timeout=1)
            port.write("*IDN?\n".encode())
            sleep(.2)
            port.close()
        except (serial.serialutil.SerialException, serial.SerialException, AssertionError) as e:
            # print(e)
            self.Com = self.find_meter_comport()
            if not self.Com:
                raise RuntimeError(self.Dev.name + " Meter Not Found.")
        self.Port.port = self.Com
        if self.Dev.value:
            cfg.dutCOM = self.Com
            cfg.dut_model = self.Model
        else:
            cfg.refCOM = self.Com
            cfg.ref_model = self.Model
        Config.save(cfg)
        self.Port.open()
        print(f"{self.Dev.name} Meter:\n"
              f" Model Number:  {self.Model}\n"
              f" Serial Number: {self.serial_num}\n"
              f" COM Port:      {self.Com}\n")

    def find_meter_comport(self) -> str:
        """Finds meter COM port. Returns None string if not found."""
        print(f"Finding {self.Dev.name} Meter...\n")
        for d in serial.tools.list_ports.comports():
            try:
                if d.name:
                    port = serial.Serial(d.name, baudrate=self.Baud, timeout=1)
                    port.write("*IDN?\n".encode())
                    sleep(.2)
                    resp = port.readline().decode()
                    if self.serial_num in resp and self.Model in resp:
                        self.Model = resp.split()[0]
                        port.close()
                        return d.name
                    else:
                        port.close()
                        continue
            except serial.SerialException:
                continue
        return ""

    def update(self, response: bytes):
        """run callback whenever value received from multimeter"""
        pass

    def read(self):
        while self.Should_Read:
            self.write("FETCH?", self.Callback)
            sleep(.05)

    def write(self, msg: str, callback=lambda x: None):
        with self.Lock:
            try:
                self.Port.write((msg + '\n').encode())
                callback(self.Port.readline())
            except IOError:
                # self.on_disconnected()
                pass
            except serial.SerialTimeoutException as e:
                self.Port.reset_input_buffer()
                self.Port.reset_output_buffer()
                log_error(e)
            except ValueError as e:
                self.Port.reset_input_buffer()
                self.Port.reset_output_buffer()
                log_error(e)
            sleep(.01)

    def change_mode(self, mode: str):
        print(f"{self.Dev.name} changing to {mode.split()[-1]}")
        self.Should_Read = False
        sleep(.01)
        with self.Lock:
            self.Port.reset_input_buffer()
            # self.Port.reset_output_buffer()
            self.Port.write((mode + '\n').encode())
            sleep(.01)
        self.Port.reset_input_buffer()
        # self.Port.reset_output_buffer()
        self.Should_Read = True
        self.Thread = Thread(target=self.read, args=())
        self.Thread.start()
        # print(f"{self.Dev.name} mode changed")

    def close(self):
        self.Should_Read = False
        while self.Thread.is_alive():
            sleep(.05)
        self.Port.close()

    def on_disconnected(self):
        self.Should_Read = False
        self.Port.close()
        sleep(.1)
        self.Port = serial.Serial(port=self.Com, baudrate=self.Baud, timeout=1)
        self.Should_Read = True
        self.Thread = Thread(target=self.read, args=())
        self.Thread.start()

    # The following should only be used with 5491B meters
    def voltage(self):
        self.change_mode("FUNC VOLT:DC")

    def frequency(self):
        self.change_mode("FUNC FREQ")

    def current(self):
        self.change_mode("FUNC CURR:DC")
