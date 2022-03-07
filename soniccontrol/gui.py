from ast import arg
import datetime
from distutils import command
import enum
import logging
import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.ttk as ttk
from matplotlib import style
from pyparsing import col
import ttkbootstrap as ttkb
from abc import ABC, abstractmethod
import time
import subprocess
import os
from sonicpackage import Command, SerialConnection, Status
from .helpers import logger



class ScriptCommand(enum.Enum):
    
    SET_FRQ: str = "frequency XXXXXXXX\n"
    SET_GAIN: str = "gain XXX\n"
    SET_KHZ: str = "setkHz\n"
    SET_MHZ: str = "setMHz\n"
    SET_SIGNAL_ON: str = "on\n"
    SET_SIGNAL_OFF: str = "off\n"
    SET_AUTO: str = "autotune\n"
    SET_HOLD: str = "hold X\n"
    STARTLOOP: str = "startloop X\n"
    ENDLOOP: str = "endloop\n"
    SET_RAMP: str = "ramp XXXXXXX,XXXXXXX,XXXX,XX\n"
    # SET_WIPE: str = ""
    # SET_PROT: str = ""
    # SET_PROT_RANGE: str = ""
    # SET_PROT_STEP: str =""
    # SET_PROT_TIME_ON: str =""
    # SET_PROT_TIME_OFF: str =""
    # SET_PROT_FRQ1: str = ""
    # SET_PROT_FRQ2: str = ""
    # SET_PROT_FRQ3: str = ""
    # SET_TUNING_STEP: str = ""
    # SET_TUNING_PAUSE: str = ""
    # SET_SCANNING_STEP: str = ""
    # SET_FLOW: str = ""
    # SET_CURRENT1: str = ""
    # SET_CURRENT2: str = ""
    # SET_SERIAL: str = ""



class HomeTabCatch(ttk.Frame):
    
    @property
    def root(self) -> tk.Tk:
        return self._root
    
    def __init__(self, parent: ttk.Notebook, root: tk.Tk, *args, **kwargs) -> None:
        """
        The Hometab is a child tab of the Notebook menu and is resonsible
        for handling and updating its children
        
        The frame is, again, splittet up into two main frames that organize
        its children
        """
        super().__init__(parent, *args, **kwargs)
        self._root: tk.Tk = root
        
        self.config(height=200, width=200)
        
        # Here follows the code regarding the TOPFRAME
        self.topframe: ttk.Labelframe = ttk.Labelframe(self, text="Manual control")
        self.control_frame: ttk.Frame = ttk.Frame(self.topframe) 
        
        # Frq frame
        self.frq_frame: ttk.Label = ttk.Label(self.control_frame)
        self.frq_spinbox: ttk.Spinbox = ttk.Spinbox(
            self.frq_frame,
            from_=600000,
            increment=100,
            to=6000000,
            textvariable=self.root.frq, 
            width=16,
            style='dark.TSpinbox',
            command=lambda: self.root.serial.sc_sendget(Command.SET_FRQ + self.root.frq.get(), self.root.thread))
        
        self.scroll_digit: ttk.Spinbox = ttk.Spinbox(
            self.frq_frame,
            from_=1,
            increment=1,
            to=6,
            validate=None,
            width=5,
            style='secondary.TSpinbox',
            command=self.set_scrolldigit)
        
        # Gain Frame
        self.gain_frame: ttk.Frame = ttk.Frame(self.control_frame)
        self.gain_spinbox: ttk.Spinbox = ttk.Spinbox(
            self.gain_frame,
            from_=0,
            increment=10,
            to=150,
            textvariable=self.root.gain,
            width=5,
            style='dark.TSpinbox',
            command=lambda: self.root.serial.sc_sendget(Command.SET_GAIN + int(self.root.gain.get()), self.root.thread))
        
        self.gain_scale: ttk.Scale = ttk.Scale(
            self.gain_frame,
            from_=0,
            to=150,
            name='gainscale',
            length=180,
            orient=tk.HORIZONTAL,
            style="primary.TScale",
            variable=self.root.gain,)
            #command=lambda: self.root.serial.sc_sendget(Command.SET_GAIN + int(self.root.gain.get()), self.root.thread))
        
        # kHz MHz Frame
        self.frq_rng_frame: ttk.Label = ttk.Label(self.control_frame)
        self.khz_button: ttkb.Radiobutton = ttkb.Radiobutton(
            self.frq_rng_frame,
            text='KHz',
            value='khz',
            variable=self.root.frq_range,
            bootstyle='dark-outline-toolbutton',
            width=12,
            command=lambda: self.root.serial.sc_sendget(Command.SET_KHZ, self.root.thread))
        
        self.mhz_button: ttkb.Radiobutton = ttkb.Radiobutton(
            self.frq_rng_frame,
            text='MHz',
            value='mhz',
            variable=self.root.frq_range,
            bootstyle='dark-outline-toolbutton',
            width=12,
            command=lambda: self.root.serial.sc_sendget(Command.SET_MHZ, self.root.thread)) 
        
        # Other children of the control frame
        self.set_val_btn: ttk.Button = ttk.Button(
            self.control_frame,
            text='Set Frequency and Gain',
            command=self.set_val,
            bootstyle='dark.TButton',)
        
        self.sonic_measure_frame: ttk.Frame = ttk.Frame(self.topframe)
        self.sonic_measure_button: ttk.Button = ttk.Button(
            self.sonic_measure_frame,
            text='Sonic measure',
            style='dark.TButton',
            image=self.root.graph_img,
            compound=tk.TOP,
            command=self.root.publish_sonicmeasure)
        
        self.serial_monitor_btn: ttk.Button = ttk.Button(
            self.sonic_measure_frame,
            text='Serial Monitor',
            style='secondary.TButton',
            width=12,
            command=self.root.publish_serial_monitor,)
        
        self.botframe: ttk.Frame = ttk.Frame(self)
        
        self.us_on_button: ttk.Button = ttk.Button(
            self.botframe,
            text='ON',
            style='success.TButton',
            width=10,
            command=lambda: self.root.serial.sc_sendget(Command.SET_SIGNAL_ON, self.root.thread))
        
        self.us_off_button: object = ttk.Button(
            self.botframe,
            text='OFF',
            style='danger.TButton',
            width=10,
            command=lambda: self.root.serial.sc_sendget(Command.SET_SIGNAL_OFF, self.root.thread))
        
        logger.info("Initialized children and object")

    def set_val(self) -> None:
        self.root.serial.sc_sendget(
            [Command.SET_GAIN + int(self.root.gain.get()),
            Command.SET_FRQ + self.root.frq.get(),], 
            self.root.thread)
            
    def attach_data(self) -> None:
        logger.info("Attaching data to Hometab")
        self.frq_spinbox.config(
            from_=self.root.sonicamp.frq_range_start,
            to=self.root.sonicamp.frq_range_stop)
            
    def publish(self) -> None:
        """ Function to build children of this frame """
        logger.info("Publishing hometab")
        self.frq_spinbox.grid(row=0, column=0, padx=10, pady=10, sticky=tk.NSEW)
        self.scroll_digit.grid(row=0, column=1, padx=10, pady=10, sticky=tk.NSEW)
        
        self.gain_spinbox.grid(row=0, column=0, padx=10, pady=10, sticky=tk.NSEW)
        self.gain_scale.grid(row=0, column=1, padx=10, pady=10, sticky=tk.NSEW)
        
        self.khz_button.grid(row=0, column=0, padx=10, pady=10, sticky=tk.NSEW)
        self.mhz_button.grid(row=0, column=1, padx=10, pady=10, sticky=tk.NSEW)
        
        self.frq_frame.pack(side=tk.TOP, expand=True, fill=tk.X)
        self.gain_frame.pack(side=tk.TOP, expand=True, fill=tk.X)
        self.frq_rng_frame.pack(side=tk.TOP, expand=True, fill=tk.X)
        self.set_val_btn.pack(side=tk.TOP, expand=True, fill=tk.X, padx=10, pady=10)
        self.sonic_measure_button.pack(side=tk.TOP, padx=10, pady=10)
        self.serial_monitor_btn.pack(side=tk.TOP, padx=10, pady=5)
        
        self.control_frame.grid(row=0, column=0, padx=10, pady=10, sticky=tk.NSEW)
        self.sonic_measure_frame.grid(row=0, column=1, padx=20, pady=20, sticky=tk.NSEW)

        self.us_on_button.grid(row=0, column=0, padx=10, pady=10, sticky=tk.NSEW)
        self.us_off_button.grid(row=0, column=1, padx=10, pady=10, sticky=tk.NSEW)

        self.topframe.pack(side=tk.TOP, padx=20, pady=20)
        self.botframe.pack(side=tk.TOP)        
            
    def set_scrolldigit(self) -> None:
        """ Function regarding the scroll digit combobox """
        self.frq_spinbox.config(
            increment = str(10 ** (int(self.scroll_digit.get())-1)))
        
        


class ScriptingTab(ttk.Frame):
    """ Scripting tab of the GUI """
    
    @property
    def root(self) -> tk.Tk:
        return self._root
    
    @property
    def serial(self) -> SerialConnection:
        return self._serial
    
    def __init__(self, parent: ttk.Notebook, root: tk.Tk, *args, **kwargs) -> None:
        """ Declare all children """
        super().__init__(parent, *args, **kwargs)
        self._root = root
        self._serial: SerialConnection = root.serial
        self.script_filepath: str
        self.save_filename: str
        self.logfilename: str
        self.logfilepath: str
        self.current_task: tk.StringVar = tk.StringVar(value='Idle')
        self.previous_task: tk.StringVar = tk.StringVar(value='Idle')
        
        self._filetypes: list[tuple] = [('Text', '*.txt'),('All files', '*'),]
        
        self.config(height=200, width=200)
        
        self.logger: logging.Logger = logging.getLogger("Scripting")
        self.formatter: logging.Formatter = logging.Formatter('%(asctime)s  %(message)s')
        self.file_handler: logging.FileHandler = logging.FileHandler(f'{datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")}_sequence.log')
        self.logger.setLevel(logging.DEBUG)
        self.file_handler.setFormatter(self.formatter)
        self.logger.addHandler(self.file_handler)
        
        self.button_frame: ttk.Frame = ttk.Frame(self)
        self.start_script_btn = ttk.Button(
            self.button_frame,
            text='Run',
            style='success.TButton',
            width=11,
            image=self.root.play_img,
            compound=tk.RIGHT,
            command=self.read_file,)
        
        self.load_script_btn: ttk.Button = ttk.Button(
            self.button_frame,
            text='Open script file',
            style='dark.TButton',
            width=15,
            command=self.load_file,)
        
        self.save_script_btn: ttk.Button = ttk.Button(
            self.button_frame,
            text='Save script file',
            style='dark.TButton',
            width=15,
            command=self.save_file,)
        
        # self.save_log_btn: ttk.Button = ttk.Button(
        #     self.button_frame,
        #     text='Specify logfile path',
        #     style='dark.TButton',
        #     width=15,
        #     command=self.open_logfile)
        
        self.sequence_status: ttkb.Floodgauge = ttkb.Floodgauge(
            self.button_frame,
            font=self.root.qtype12,
            length=160,
            mode=ttkb.INDETERMINATE,
            orient=ttkb.HORIZONTAL,
            bootstyle=ttkb.DARK,) 
        
        self.scripting_frame: ttk.Labelframe = ttk.Labelframe(
            self,
            text="Script Editor",
            style="dark.TLabelframe",
            padding=(5,5,5,5),)
        
        self.scripttext: tk.Text = tk.Text(
            self.scripting_frame,
            autoseparators=False,
            background='white',
            setgrid=False,
            width=35,
            padx=5,
            pady=5,
            font=("Consolas", 12))
        
        self.scrollbar: ttk.Scrollbar = ttk.Scrollbar(
            self.scripting_frame,
            orient='vertical',
            command=self.scripttext.yview)  
        
        self.show_log_console: ttk.Button = ttk.Button(
            self.scripting_frame,
            text='Show log console',
            style="secondary.TButton",
            command=self.show_console)
        
        self.script_guide_btn = ttk.Button(
            self.scripting_frame,
            text='Scripting Guide',
            style='dark.TButton',
            command=lambda: ScriptingGuide(self.root, self.scripttext))

        self.task_frame = ttk.Frame(self)
        self.static_prevtask_label = ttk.Label(
            self.task_frame,
            text='Previous Task:',)
        
        self.prev_task_label = ttk.Label(
            self.task_frame,
            textvariable=self.previous_task,)
        
        self.static_curtask_label = ttk.Label(
            self.task_frame,
            text='Current Task:')
        
        self.cur_task_label = ttk.Label(
            self.task_frame,
            textvariable=self.current_task)
        
        logger.info("Initialized scripting tab")

    def publish(self):
        # Button Frame
        logger.info("Publishing scripting tab")
        self.button_frame.pack(anchor=tk.N, side=tk.LEFT, padx=5, pady=5)
        for child in self.button_frame.winfo_children():
            child.pack(side=tk.TOP, padx=5, pady=5)

        #Scripting Frame
        self.scripting_frame.pack(anchor=tk.N ,side=tk.RIGHT ,padx=5, pady=5, expand=True, fill=tk.X)
        self.scripttext.grid(row=0, column=0, columnspan=2)
        self.show_log_console.grid(row=1, column=0, padx=5, pady=5)
        self.script_guide_btn.grid(row=1, column=1, padx=5, pady=5)
        
        #Task Frame
        self.task_frame.pack(side=tk.BOTTOM, padx=10, pady=10)
        self.static_prevtask_label.grid(row=0, column=0)
        self.prev_task_label.grid(row=1, column=0)
        self.static_curtask_label.grid(row=0, column=1)
        self.cur_task_label.grid(row=1, column=1)
    
    def show_console(self):
        pass
    
    def load_file(self) -> None:
        self.script_filepath = filedialog.askopenfilename(defaultextension='.txt', filetypes=self._filetypes)
        with open(self.script_filepath, 'r') as f:
            self.scripttext.delete(0, tk.END)
            self.scripttext.insert(tk.INSERT, f.read())
        logger.info("Loaded file")
    
    def save_file(self) -> None:
        self.save_filename = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=self._filetypes)
        with open(self.save_filename, 'w') as f:
            f.write(self.scripttext.get(0, tk.END))
    
    def open_logfile(self) -> None:
        self.logfilepath = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=self._filetypes)
    
    def close_file(self) -> None:
        self.run: bool = False
        self.scripttext.tag_delete("currentLine", 1.0, tk.END)
        self.start_script_btn.configure(
            text='Run',
            style='success.TButton',
            image=self.root.play_img,
            command=self.read_file)
        self.sequence_status.stop()
        self.current_task.set('Idle')
        self.previous_task.set('Idle')
        self.root.notebook.enable_children()
        self.scripttext.config(state=tk.NORMAL)
        self.load_script_btn.config(state=tk.NORMAL)
        self.save_script_btn.config(state=tk.NORMAL)
        # self.save_log_btn.config(state=tk.NORMAL)
        self.script_guide_btn.config(state=tk.NORMAL)
        self.sequence_status.config(text=None)
        self.serial.send_and_get(Command.SET_SIGNAL_OFF)
        self.root.thread.resume()
    
    def read_file(self):
        self.run: bool = True
        self.root.thread.pause()
        self.start_script_btn.configure(
            text='Stop',
            style='danger.TButton',
            image=self.root.pause_img,
            command=self.close_file)
        self.sequence_status.start()
        self.root.notebook.disable_children(self)
        self.scripttext.config(state=tk.DISABLED)
        self.load_script_btn.config(state=tk.DISABLED)
        self.save_script_btn.config(state=tk.DISABLED)
        # self.save_log_btn.config(state=tk.DISABLED)
        self.script_guide_btn.config(state=tk.DISABLED)
        self.serial.send_and_get(Command.SET_SIGNAL_ON)
        
        self.start_sequence()
    
    def start_sequence(self) -> None:
        logger.info("started sequence")
        
        self.commands: list[str] = []
        self.args_: list[str] = []
        self.loops: list[list[int]] = [[]]
        self.loop_index: int = 0
        
        line_list: list[str] = self.scripttext.get(1.0, tk.END).splitlines()
        self.parse_commands(line_list)
        
        for i, command in enumerate(self.commands):
            if command == "startloop":
                loopdata = [i, int(self.args_[i][0])]
                self.loops.insert(i, loopdata)
            elif command == "endloop":
                self.loops.insert(i, [])
                for loop in reversed(self.loops):
                    if len(loop) == 2:
                        loop.insert(2, i)
                        break
            elif command == "hold":
                self.loops.insert(i, [])
            elif command == "ramp":
                self.loops.insert(i, [])
                
                start: int = int(self.args_[i][0])
                stop: int = int(self.args_[i][1])
                step: int = int(self.args_[i][2])
                delay: int = int(self.args_[i][3])
                
                if start > stop:
                    frq_list: list = list(range(stop, start, step))
                else:
                    frq_list: list = list(range(start, stop, step))
            else:
                self.loops.insert(i, [])
        
        i = 0
        while i < len(self.commands) and self.run:
            self.sequence_status["text"] = self.current_task.get()
            self.scripttext.tag_remove('currentLine', 1.0, "end")
            self.scripttext.tag_add('currentLine', f"{i}.0", f"{i}.end")
            self.scripttext.tag_configure('currentLine', background="#3e3f3a", foreground="#dfd7ca")
            if self.commands[i] == 'startloop':
                if self.loops[i][1]:
                    self.loops[i][1] =- 1
                    i += 1
                else:
                    i = self.loops[i][2] + 1
            elif self.commands[i] == 'endloop':
                for loop in self.loops:
                    if loop[2] == i:
                        for j in range(self.loops[0]+1, self.loops[2]):
                            if self.loops[j]:
                                self.loops[j][1] = int(self.args_[j][0])
                        i = loop[0]
            else:
                self.exec_command(i)
                i += 1
        self.close_file()
        
    def exec_command(self, counter: int) -> None:
        self.current_task.set(f"{self.commands[counter]} {str(self.args_[counter])}")
        self.root.update()
        if counter > 0:
            self.previous_task.set(f"{self.commands[counter-1]} {self.args_[counter-1]}")
        status = Status.construct_from_str(self.serial.send_and_get(Command.GET_STATUS))
        self.logger.info(f"{str(self.commands[counter])}\t{str(self.args_[counter])}\t{status.frequency}\t{status.gain}")
        if self.commands[counter] == "frequency":
            logger.info("executing frq command")
            self.serial.send_and_get(Command.SET_FRQ + self.args_[counter])#, self.root.thread)
        elif self.commands[counter] == "gain":
            logger.info("executing gain")
            self.serial.send_and_get(Command.SET_GAIN + self.args_[counter][0])#, self.root.thread)
        elif self.commands[counter] == "ramp":
            logger.info("executing ramp command")
            self.start_ramp(self.args_[counter])
        elif self.commands[counter] == "hold":
            logger.info("executing hold command")
            now = datetime.datetime.now()
            target = now + datetime.timedelta(milliseconds=int(self.args_[counter][0]))
            while now < target:
                time.sleep(0.02)
                now = datetime.datetime.now()
                # self.root.attach_data()
        elif self.commands[counter] == "on":
            logger.info("executing on command")
            self.serial.send_and_get(Command.SET_SIGNAL_ON)#, self.root.thread)
            # self.root.attach_data()
        elif self.commands[counter] == "off":
            logger.info("executing off command")
            self.serial.send_and_get(Command.SET_SIGNAL_OFF)#, self.root.thread)
            # self.root.attach_data()
        elif self.commands[counter] == "setMHz":
            logger.info("executing mhz command")
            self.serial.send_and_get(Command.SET_MHZ)#, self.root.thread)
        elif self.commands[counter] == "setkHz":
            logger.info("executing khz command")
            self.serial.send_and_get(Command.SET_KHZ)#, self.root.thread)
        elif self.commands[counter] == "autotune":
            logger.info("executing auto command")
            self.serial.send_and_get(Command.SET_AUTO)#, self.root.thread)
    
    def start_ramp(self, args_: list) -> None:
        logger.info("starting ramp")
        start = int(args_[0])
        stop = int(args_[1])
        step = int(args_[2])
        delay = int(args_[3])
        
        if start > stop:
            for frq in range(start, stop, -step):
                self.current_task.set(f"Ramp is @ {frq/1000}kHz")
                self.logger.info(f"ramp\t{start},{stop},{step}\t{frq}")
                self.root.status_frame_catch.frq_meter["amountused"] = frq
                self.serial.sc_sendget(Command.SET_FRQ + frq, self.root.thread)
        else:
            for frq in range(start, stop, step):
                self.current_task.set(f"Ramp is @ {frq/1000}kHz")
                self.logger.info(f"ramp\t{start},{stop},{step}\t{frq}")
                self.root.status_frame_catch.frq_meter["amountused"] = frq
                self.serial.sc_sendget(Command.SET_FRQ + frq, self.root.thread)
                
    
    def parse_commands(self, line_list: list) -> None:
        logger.info("Parsing commands")
        for line in line_list:
            if ' ' in line:
                self.commands.append(line.split(' ')[0])
                self.args_.append(line.split(' ')[1].split(','))
            else:
                self.commands.append(line)
                self.args_.append(None)
    
    def attach_data(self) -> None:
        pass



class ScriptingGuide(tk.Toplevel):
    
    def __init__(self, root: tk.Tk, scripttext: tk.Text, *args, **kwargs):
        super().__init__(root, *args, **kwargs)
        self.title('Function Helper')

        self.scripttext: tk.Text = scripttext
        
        # Headings
        self.heading_frame: ttk.Frame = ttk.Frame(self)
        self.heading_command = ttk.Label(
            self.heading_frame, 
            anchor=tk.W, 
            justify=tk.CENTER, 
            text='Command',
            width=15,
            style="dark.TLabel",
            font="QTypeOT-CondMedium 15 bold",)
        self.heading_command.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
        
        self.heading_arg = ttk.Label(
            self.heading_frame, 
            anchor=tk.W, 
            justify=tk.CENTER,
            width=15,
            style="info.TLabel",
            text='Arguments', 
            font="QTypeOT-CondMedium 15 bold",)
        self.heading_arg.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NSEW)
        
        self.heading_description = ttk.Label(
            self.heading_frame, 
            anchor=tk.W, 
            justify=tk.CENTER,
            width=15,
            style="primary.TLabel",
            text='Description',
            font="QTypeOT-CondMedium 15 bold",)
        self.heading_description.grid(row=0, column=2, padx=5, pady=5, sticky=tk.NSEW)
        self.heading_frame.pack(side=tk.TOP, padx=5, pady=5, anchor=tk.W, expand=True, fill=tk.X)
        
        self.hold_btn: ScriptingGuideRow = ScriptingGuideRow(
            self,
            btn_text="hold",
            arg_text="[1-100.000] in [seconds]",
            desc_text="Hold the last state for X seconds",
            command=lambda: self.insert_command(ScriptCommand.SET_HOLD),)
        self.hold_btn.pack(side=tk.TOP, padx=5, pady=5, anchor=tk.W)
        
        self.frq_btn: ScriptingGuideRow = ScriptingGuideRow(
            self,
            btn_text='frequency',
            arg_text='[50.000-1.200.000] for kHz in [Hz]\n [600.000-6.000.000] for MHz in [Hz]',
            desc_text='Change to the indicated frequency in Hz',
            command = lambda: self.insert_command(ScriptCommand.SET_FRQ))
        self.frq_btn.pack(side=tk.TOP, padx=5, pady=5, anchor=tk.W)
        
        self.gain_btn: ScriptingGuideRow = ScriptingGuideRow(
            self,
            btn_text='gain',
            arg_text='[1-150] in [%]',
            desc_text='Change to the selected gain in %',
            command = lambda: self.insert_command(ScriptCommand.SET_GAIN))
        self.gain_btn.pack(side=tk.TOP, padx=5, pady=5, anchor=tk.W)
        
        self.khz_btn: ScriptingGuideRow = ScriptingGuideRow(
            self,
            btn_text='setkHz',
            arg_text=None,
            desc_text='Change to the kHz range amplifier',
            command = lambda: self.insert_command(ScriptCommand.SET_KHZ))
        self.khz_btn.pack(side=tk.TOP, padx=5, pady=5, anchor=tk.W)
        
        self.mhz_btn: ScriptingGuideRow = ScriptingGuideRow(
            self,
            btn_text='setMHz',
            arg_text=None,
            desc_text='Change to the MHz range amplifier',
            command = lambda: self.insert_command(ScriptCommand.SET_MHZ))
        self.mhz_btn.pack(side=tk.TOP, padx=5, pady=5, anchor=tk.W)
        
        self.on_btn: ScriptingGuideRow = ScriptingGuideRow(
            self,
            btn_text='on',
            arg_text=None,
            desc_text='Activate US emission',
            command = lambda: self.insert_command(ScriptCommand.SET_SIGNAL_ON))
        self.on_btn.pack(side=tk.TOP, padx=5, pady=5, anchor=tk.W)
        
        self.off_btn: ScriptingGuideRow = ScriptingGuideRow(
            self,
            btn_text='off',
            arg_text=None,
            desc_text='Deactivate US emission',
            command = lambda: self.insert_command(ScriptCommand.SET_SIGNAL_OFF))
        self.off_btn.pack(side=tk.TOP, padx=5, pady=5, anchor=tk.W)
        
        self.startloop_btn: ScriptingGuideRow = ScriptingGuideRow(
            self,
            btn_text='startloop',
            arg_text='[2-10.000] as an [integer]',
            desc_text='Start a loop for X times',
            command = lambda: self.insert_command(ScriptCommand.STARTLOOP))
        self.startloop_btn.pack(side=tk.TOP, padx=5, pady=5, anchor=tk.W)
        
        self.endloop_btn: ScriptingGuideRow = ScriptingGuideRow(
            self,
            btn_text='endloop',
            arg_text=None,
            desc_text='End the loop here',
            command = lambda: self.insert_command(ScriptCommand.ENDLOOP))
        self.endloop_btn.pack(side=tk.TOP, padx=5, pady=5, anchor=tk.W)
        
        self.ramp_btn: ScriptingGuideRow = ScriptingGuideRow(
            self,
            btn_text='ramp',
            arg_text='start f [Hz], stop f [Hz], step size [Hz], delay [s]',
            desc_text='Create a frequency ramp with a start frequency, a stop frequency,\n a step size and a delay between steps',
            command = lambda: self.insert_command(ScriptCommand.SET_RAMP))
        self.ramp_btn.pack(side=tk.TOP, padx=5, pady=5, anchor=tk.W)
        
        self.autotune_btn: ScriptingGuideRow = ScriptingGuideRow(
            self,
            btn_text='autotune',
            arg_text=None,
            desc_text='Start the autotune protocol. This should be followed by "hold"\n commands, otherwise the function will be stopped.',
            command = lambda: self.insert_command(ScriptCommand.SET_AUTO))
        self.autotune_btn.pack(side=tk.TOP, padx=5, pady=5, anchor=tk.W)
        
        self.disclaimer_label = ttk.Label(
            self, 
            text='To insert a function at the cursor position, click on the respective button', 
            font=('TkDefaultFont', 11, 'bold'))
        self.disclaimer_label.pack(side=tk.TOP, expand=True, fill=tk.X, padx=5, pady=5)
        
        
    def insert_command(self, command: ScriptCommand) -> None:
        self.scripttext.insert(self.scripttext.index(tk.INSERT), command.value)
        

class ScriptingGuideRow(ttk.Frame):
    
    def __init__(self, parent: ttk.Frame, btn_text: str, arg_text: str, desc_text: str, command,*args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        
        self.command_btn: ttk.Button = ttk.Button(
            self,
            width=15,
            style="dark.TButton",
            text=btn_text,
            command=command)
        self.command_btn.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
        
        if arg_text:
            # self.arg_entry: ttk.Entry = ttk.Entry(
            #     self,
            #     width=15,
            #     justify=tk.LEFT,
            #     style="info.TEntry",)
            # self.arg_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NSEW)

            self.arg_label: ttk.Label = ttk.Label(
                self,
                style='inverse.info.TLabel',
                text=arg_text)
            self.arg_label.grid(row=0, column=2, padx=5, pady=5, sticky=tk.NSEW)  
        
        
        self.desc_label: ttk.Label = ttk.Label(
            self,
            text=desc_text,
            style='inverse.primary.TLabel')
        self.desc_label.grid(row=0, column=3, padx=5, pady=5, sticky=tk.NSEW)


class ConnectionTab(ttk.Frame):
    
    @property
    def root(self) -> tk.Tk:
        return self._root
    
    def __init__(self, parent: ttk.Notebook, root: tk.Tk, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self._root = root
        
        self.topframe: ttk.Frame = ttk.Frame(self, padding=(10, 10, 10, 10))
        self.heading_frame: ttk.Frame = ttk.Frame(self.topframe)
        
        self.subtitle: ttk.Label = ttk.Label(self.heading_frame, padding=(0, 10, 0, 0))
        
        self.heading1 = ttk.Label(
            self.heading_frame, 
            padding=(10,0,0,10),
            font = self.root.qtype30)
        
        self.heading2 = ttk.Label(
            self.heading_frame,
            padding=(0,0,10,10),
            font = self.root.qtype30b)
        
        self.control_frame = ttk.Frame(self.topframe)
        
        self.connect_button = ttkb.Button(
            self.control_frame, 
            width = 10,
            style="success.TButton")
        
        self.ports_menue = ttk.Combobox(
            master=self.control_frame,
            textvariable=self.root.port,
            values=None,
            width=7,
            style = "dark.TCombobox",
            state=tk.READABLE)
        
        self.refresh_button = ttkb.Button(
            self.control_frame, 
            bootstyle="secondary-outline",
            image=self.root.refresh_img, 
            command = self.refresh)
        
        self.botframe: ttk.Frame = ttk.Frame(self)
        # self.firmware_tree: ttk.Treeview = ttkb.Treeview(
        #     self.botframe,
        #     columns=("Title", "Value"),
        #     style="dark.TTreeview",
        #     height=3,
        #     selectmode=None,)
        # self.firmware_tree.column('Title',anchor='sw', width=80)
        # self.firmware_tree.column('Value',anchor='sw', width=80)
        # self.firmware_tree.heading('Title', text='Title', anchor='sw',)
        # self.firmware_tree.heading('Value', text='Value', anchor='sw',)
        self.firmware_frame: ttk.Labelframe = ttk.Labelframe(
            self.botframe,
            text='Firmware',)
        
        self.firmware_label: ttk.Label = ttk.Label(
            self.firmware_frame,
            justify=tk.CENTER,
            style='dark.TLabel')
        
        self.flash_frame = ttk.Labelframe(
            self.botframe, 
            height=250, 
            text='Update Firmware', 
            width=200)
        
        self.file_entry = ttk.Button(
            self.flash_frame, 
            text="Specify path for Firmware file", 
            width=20, 
            style="dark.TButton",
            command=self.hex_file_path_handler)
        
        self.hex_file_path = tk.StringVar()
        
        # self.firmware_progress_text = ttk.Label(
        #     self, text="Uploading...", font=self.root.qtype12)
        
        self.upload_button = ttk.Button(
            self.flash_frame, 
            style='dark.TButton',
            width=20,
            text='Upload Firmware', 
            command=self.upload_file)
        
        logger.info("Initialized children and object connectiontab")
    
    def attach_data(self) -> None:
        logger.info("attaching data")
        self.subtitle["text"] = "You are connected to"
        self.heading1["text"] = self.root.sonicamp.amp_type[:5]
        self.heading2["text"] = self.root.sonicamp.amp_type[5:]
        self.connect_button.config(
            bootstyle="danger",
            text="Disconnect",
            command=self.disconnect,)
        self.ports_menue.config(
            textvariable=self.root.port,
            values=self.root.serial.device_list,)
        self.firmware_label["text"] = self.root.sonicamp.firmware[0] #!Here
        for child in self.flash_frame.children.values():
            child.configure(state=tk.NORMAL)
        
    def abolish_data(self) -> None:
        logger.info("abolishing data")
        self.subtitle["text"] = "Please connect to a SonicAmp system"
        self.heading1["text"] = "not"
        self.heading2["text"] = "connected"
        self.connect_button.config(
            bootstyle="success",
            text="Connect",
            command=self.root.__reinit__,)
        self.ports_menue.config(
            textvariable=self.root.port,
            values=self.root.serial.device_list,)
        self.firmware_label["text"] = ""
        for child in self.flash_frame.children.values():
            child.configure(state=tk.DISABLED)

    def refresh(self) -> None:
        self.ports_menue['values'] = self.root.serial.get_ports()
    
    def disconnect(self) -> None:
        self.abolish_data()
        self.root.serial.disconnect()
        self.root.publish_disconnected()
        self.root.thread.pause()
    
    def publish(self) -> None:
        logger.info("Publishing connectiontab")
        for child in self.children.values():
            child.pack()
        
        self.subtitle.grid(row=0, column=0, columnspan=2, sticky=tk.S)
        self.heading1.grid(row=1, column=0, columnspan=1, sticky=tk.E)
        self.heading2.grid(row=1, column=1, columnspan=1, sticky=tk.W)
        self.heading_frame.pack(padx=10, pady=20, expand=True)

        self.ports_menue.grid(row=0, column=0, columnspan=2, pady=10, padx=5, sticky=tk.NSEW)        
        self.connect_button.grid(row=0, column=2,columnspan=1, pady=10, padx=5, sticky=tk.NSEW)
        self.refresh_button.grid(row=0, column=3 ,columnspan=1,  pady=10, padx=5, sticky=tk.NSEW)
        self.control_frame.pack(padx=10, pady=20, expand=True)
    
        self.firmware_frame.grid(row=0, column=0, padx=10, pady=10)
        self.firmware_label.pack()
        self.file_entry.pack(padx=10, pady=10, side=tk.TOP)
        self.upload_button.pack(padx=10, pady=10, side=tk.TOP)
        self.flash_frame.grid(row=0, column=1, padx=10, pady=10)
    
    def hex_file_path_handler(self):
        self.hex_file_path = filedialog.askopenfilename(defaultextension=".hex", filetypes=(("HEX File", "*.hex"),))
        if self.hex_file_path[-4:] == ".hex":
            self.file_entry.config(style="success.TButton", text="File specified and validated")
        else:
            messagebox.showerror("Wrong File", "The specified file is not a validated firmware file. Please try again with a file that ends with the format \".hex\"")
            self.file_entry.config(style="danger.TButton", text="File is not a firmware file")

    def upload_file(self):
        if self.root.serial.is_connected:
            if self.hex_file_path:
                port = self.ser.port
                self.ser.close()
                cur_dir = os.getcwd()
                # self.firmware_progress_text.pack(padx=10, pady=10)
                try:
                    command = f"\"{cur_dir}/avrdude/avrdude.exe\" -v -patmega328p -carduino -P{port} -b115200 -D -Uflash:w:\"{self.hex_file_path}\":i"
                    msgbox = messagebox.showwarning("Process about to start", "The program is about to flash a new firmware on your device, please do NOT disconnect or turn off your device during that process")
                    if msgbox:
                        output = subprocess.run(command, shell=True)
                        self.file_entry.configure(style="dark.TButton", text="Specify the path for the Firmware file")
                        # self.firmware_progress_text.pack_forget()
                        self.connectPort(port)
                    else:
                        messagebox.showerror("Error", "Cancled the update")
                except WindowsError:
                    messagebox.showerror("Error", "Something went wrong, please try again. Maybe restart the device and the program")
            else:
                messagebox.showerror("Couldn't find file", "Please specify the path to the firmware file, before flashing your SonicAmp")
        else:
            messagebox.showerror("Error", "No connection is established, please recheck all connections and try to reconnect in the Connection Tab. Make sure the instrument is in Serial Mode.")



class InfoTab(ttk.Frame):
    
    INFOTEXT = (
        "Welcome to soniccontrol, a light-weight application to\n" 
        "control sonicamp systems over the serial interface. \n"
        "For help, click the \"Manual\" button below\n"
        "\n"
        "(c) usePAT G.m.b.H\n")
    
    @property
    def root(self) -> tk.Tk:
        return self._root
    
    def __init__(self, parent: ttk.Notebook, root: tk.Tk, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self._root = root
        self.soniccontrol_logo_frame: ttk.Frame = ttk.Frame(self)
        self.soniccontrol_logo1 = ttk.Label(
            self.soniccontrol_logo_frame,
            text = "sonic",
            padding=(10,0,0,10),
            font = "QTypeOT-CondLight 30")
        
        self.soniccontrol_logo2 = ttk.Label(
            self.soniccontrol_logo_frame,
            text = 'crash',
            padding=(0,0,0,10),
            font = "QTypeOT-CondBook 30 bold")
        
        self.info_label = ttk.Label(self, text=InfoTab.INFOTEXT)
        
        self.controlframe = ttk.Frame(self)
        self.manual_btn = ttk.Button(
            self.controlframe,
            text='Help Manual',
            command=self.open_manual)
        
        # self.dev_btn = ttk.Button(
        #     self.controlframe,
        #     text='I\'m a developer...',
        #     command=self.root.publish_serial_monitor,
        #     style='outline.dark.TButton')
        
        logger.info("Initialized children and object infotab")
        
    def publish(self) -> None:
        logger.info("publishing infotab")
        self.soniccontrol_logo1.grid(row=0, column=0)
        self.soniccontrol_logo2.grid(row=0, column=1)
        self.soniccontrol_logo_frame.pack(padx=20, pady=20)
        self.info_label.pack()
        self.manual_btn.grid(row=0, column=0, padx=5, pady=10)
        # self.dev_btn.grid(row=0, column=1, padx=5, pady=10)
        self.controlframe.pack()
    
    def open_manual(self) -> None:
        pass
    
    def attach_data(self) -> None:
        pass
