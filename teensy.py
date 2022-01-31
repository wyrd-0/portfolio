"""
Designed to rely upon a config file for initial setup
"""


import serial
import serial.tools.list_ports
import threading
from time import sleep
from config import Config


class Teensy:
    """Teensy class for generic teensy connections.
    Parameters can be modified from within config.config.json"""

    def __init__(self):
        cfg: Config = Config.get_instance()
        self.Baud = cfg.teensyBAUD
        self.Com = cfg.teensyCOM
        self.Port = serial.Serial(port=None, baudrate=self.Baud, timeout=1)
        self.Lock = threading.Lock()

    def connect(self):
        cfg: Config = Config.get_instance()
        """Search for Teensy.
        Raise RuntimeError if unable to find properly configured device"""
        try:
            port = serial.Serial(port=self.Com, baudrate=self.Baud, timeout=1)
            port.write('V|'.encode())
            sleep(.2)
            resp = port.readline().decode()
            assert "MAF" in resp
            print(resp)
            port.close()
        except (serial.SerialException, AssertionError):
            self.Com = self.find_teensy()
            if not self.Com:
                raise RuntimeError("Teensy Not Found.")
            cfg: Config = Config.get_instance()
            self.Port.port, cfg.teensyCOM = self.Com, self.Com
        self.Port.port = self.Com
        Config.save(cfg)
        self.Port.open()

    def find_teensy(self) -> str:
        """Finds teensy COM port. Returns None string if not found."""
        print("Finding teensy")
        for dev in serial.tools.list_ports.comports():
            try:
                port = serial.Serial(dev.name, baudrate=self.Baud, timeout=1)
                port.write('V|'.encode())
                sleep(.1)
                resp = port.readline().decode()
                if not resp:
                    continue
                else:
                    print(f" Teensy Version: {resp}")
                    port.close()
                    return dev.name
            except serial.SerialException:
                continue
        return ''

    def send_command(self, command):
        try:
            self.write(command)
        except IOError:
            self.on_disconnected()

    def read(self):
        return self.Port.read().decode()

    def write(self, msg: str):
        with self.Lock:
            self.Port.write(msg.encode())

    def close(self):
        self.Port.close()

    def on_disconnected(self):
        pass

    def set_vfd(self, frq: int):
        self.write(f'FRQ={frq}|')
