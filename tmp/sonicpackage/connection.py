from ctypes import LittleEndianStructure
from os import stat
import serial
import serial.tools.list_ports
import time
import sys
import signal
import queue



class SerialConnection():

    LINE = 'line'
    BLOCK = 'block'

    def __init__(self):
        self.port = ''
        self.baudrate = 115200
        self.is_connected = False
        self.queue = queue.Queue()
        self.device_list = self.get_ports()
        

    def get_ports(self):      
        port_list = [port.device for index, port in enumerate(serial.tools.list_ports.comports(), start=0) if port.device != 'COM1']
        port_list.insert(0, '-')
        self.device_list = port_list
        return port_list


    def connect_to_port(self, auto=False, port=None):
        
        if len(self.device_list) == 2 and auto == True:
            self.port = self.device_list[1]
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.3)    
            self.is_connected = True
        elif port:
            self.ser = serial.Serial(port, self.baudrate, timeout=0.3)
            self.is_connected = True
        else:
            print("error")
            self.is_connected = False
        
        time.sleep(6)
        self.initialize()
    

    def initialize(self):
        self.send_message('!SERIAL', SerialConnection.LINE, True, 0.5)
        


    def send_message(self, message, read_mode='line', flush=False, delay=0.1):
        try:
            print(f'Sende nachricht: {message}')
            if self.ser.is_open:
                if flush:
                    self.ser.flushInput()
                
                self.ser.write(f"{message}\n".encode())
                time.sleep(delay)
                
                if read_mode == SerialConnection.LINE:
                    answer = self.ser.readline().rstrip().decode()
                    print(answer)
                    return answer
                
                else:
                    answer = self.ser.read(255).rstrip().decode()
                    print(answer)
                    return answer
                
            else:
                return False

        except:
            return False

    
    def disconnect(self):
        self.ser.close()
        


        
class SonicAmp():

    def __init__(self, serial):
        
        self.serial = serial
        self.info = {}
        self.modules = {}


    def get_info(self):
        if self.serial.is_connected:
            self.info = {
                'port':     self.serial.port,
                'type':     self.serial.send_message('?type', flush=True, delay=0),
                'connection':   'Connected',
                'signal':       'Off',
                'error':        'No Error',
                'firmware': self.serial.send_message('?info', read_mode='block', flush=True, delay=0.5),
                'modules' : self.get_modules([bool(int(module)) for module in self.serial.send_message('=', delay=0.35).split('=')]),
                'status':   {}
            }
        else:
            self.info = {
                'port':         self.serial.port,
                'type':         False,
                'connection':   'No Connection',
                'signal':       '',
                'error':        '',
                'firmware':     False,
                'modules':      False,
                'status':   {
                    'error':            False,
                    'frequency':        False,
                    'gain':             False,
                    'current_protocol': False,
                    'wipe_mode':        False
                }
            }
        
        if self.info['type'] == 'soniccatch':
            self.info['frq rng start'] = 600000
            self.info['frq rng stop'] = 6000000
            
        elif self.info['type'] == 'sonicwipe':
            self.info['frq rng start'] = 50000
            self.info['frq rng stop'] = 1200000
        
        else:
            pass
        
        

    
    def get_modules(self, module_list):
        self.modules = { 
            'buffer':       module_list[0],
            'DISPLAY':      module_list[1],
            'EEPROM':       module_list[2],
            'FRAM':         module_list[3],
            'I_CURRENT':    module_list[4],
            'CURRENT1':     module_list[5],
            'CURRENT2':     module_list[6],
            'IO_SERIAL':    module_list[7],
            'THERMO_EXT':   module_list[8],
            'THERMO_INT':   module_list[9],
            'KHZ':          module_list[10],
            'MHZ':          module_list[11],
            'PORTEXPANDER': module_list[12],
            'PROTOCOL':     [self.get_protocols(module_list[13])],
            'PROTOCOL_FIX': module_list[14],
            'RELAIS':       module_list[15],
            'SONSENS':      module_list[16],
            'SCANNING':     module_list[17],
            'TUNING':       module_list[18],
            'SWITCH':       module_list[19],
            'SWITCH2':      module_list[20],
        }

        return self.modules

    
    def get_status(self, status):
        self.info['status'] = {
            'error':            status[0],
            'frequency':        status[1],
            'gain':             status[2],
            'current_protocol': self.get_current_protocol(status[3]),
            'wipe_mode':        bool(status[4])

        }
        return self.info['status']
    

    def get_current_protocol(self, protocol_string):
        if protocol_string == 100:
            return 'fix'
        elif protocol_string == 101:
            return None
        else:
            return protocol_string 


    def get_protocols(self, protocols):
        return protocols


