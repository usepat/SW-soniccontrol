from soniccontrol_gui.widgets.message_box import DialogOptions



RIGHT_NOTEBOOK = "right_notebook"
LEFT_NOTEBOOK = "left_notebook"
LOGGING_NOTEBOOK = "logging_notebook"
MEASURING_NOTEBOOK = "measuring_notebook"

HOME_TAB = "left_notebook.Home_tab"
SERIAL_MONITOR_TAB = "left_notebook.Serial Monitor_tab"
PROCEDURES_TAB = "left_notebook.Procedures_tab"
SCRIPTING_TAB = "left_notebook.Scripting_tab"
SETTINGS_TAB = "left_notebook.Settings_tab"
FLASHER_TAB = "left_notebook.Flasher_tab"
INFO_TAB = "right_notebook.Info_tab"
SONIC_MEASURE_TAB = "right_notebook.Sonic Measure_tab"
LOGS_TAB = "right_notebook.Logs_tab"
CONFIGURATION_TAB = "left_notebook.Configuration_tab"


# Connection constants
CONNECTION_PORTS_COMBOBOX = 'connection.ports_combobox'
CONNECTION_CONNECT_VIA_URL_BUTTON = 'connection.connect_via_url_button'
CONNECTION_CONNECT_TO_SIMULATION_BUTTON = 'connection.connect_to_simulation_button'

# Home constants
HOME_DEVICE_TYPE_LABEL = 'home.device_type_label'
HOME_FIRMWARE_VERSION_LABEL = 'home.firmware_version_label'
HOME_PROTOCOL_VERSION_LABEL = 'home.protocol_version_label'
HOME_DISCONNECT_BUTTON = 'home.disconnect_button'
HOME_FREQUENCY_ENTRY = 'home.frequency_entry'
HOME_SIGNAL_BUTTON = 'home.signal_button'
HOME_GAIN_VAR = 'home.gain_var'
HOME_GAIN_ENTRY = 'home.gain_entry'
HOME_SEND_BUTTON = 'home.send_button'

# Serial Monitor constants
SERIAL_MONITOR_READ_BUTTON = 'serial_monitor.read_button'
SERIAL_MONITOR_COMMAND_LINE_INPUT_ENTRY = 'serial_monitor.command_line_input_entry'
SERIAL_MONITOR_SEND_BUTTON = 'serial_monitor.send_button'
SERIAL_MONITOR_SCROLL_FRAME = 'serial_monitor.scroll_frame'
SERIAL_MONITOR_LOADING_LABEL = 'serial_monitor.loading_label'

# Editor constants
EDITOR_TEXT_EDITOR = 'editor.text_editor'
EDITOR_CURRENT_TASK_LABEL = 'editor.current_task_label'
EDITOR_START_PAUSE_CONTINUE_BUTTON = 'editor.start_pause_continue_button'
EDITOR_SINGLE_STEP_BUTTON = 'editor.single_step_button'
EDITOR_STOP_BUTTON = 'editor.stop_button'

# Status Bar constants
STATUS_BAR_MODE_LABEL = 'status_bar.mode_label'
STATUS_BAR_FREQ_LABEL = 'status_bar.freq_label'
STATUS_BAR_GAIN_LABEL = 'status_bar.gain_label'
STATUS_BAR_PROCEDURE_LABEL = 'status_bar.procedure_label'
STATUS_BAR_TEMPERATURE_LABEL = 'status_bar.temperature_label'
STATUS_BAR_URMS_LABEL = 'status_bar.urms_label'
STATUS_BAR_IRMS_LABEL = 'status_bar.irms_label'
STATUS_BAR_PHASE_LABEL = 'status_bar.phase_label'
STATUS_BAR_SIGNAL_LABEL = 'status_bar.signal_label'

# Status Panel constants
STATUS_PANEL_FREQ_METER = 'status_panel.freq_meter'
STATUS_PANEL_GAIN_METER = 'status_panel.gain_meter'
STATUS_PANEL_TEMP_METER = 'status_panel.temp_meter'
STATUS_PANEL_URMS_LABEL = 'status_panel.urms_label'
STATUS_PANEL_IRMS_LABEL = 'status_panel.irms_label'
STATUS_PANEL_PHASE_LABEL = 'status_panel.phase_label'
STATUS_PANEL_SIGNAL_LABEL = 'status_panel.signal_label'

# Configuration constants
CONFIGURATION_ADD_CONFIG_BUTTON = 'configuration.add_config_button'
CONFIGURATION_CONFIG_ENTRY = 'configuration.config_entry'
CONFIGURATION_SAVE_CONFIG_BUTTON = 'configuration.save_config_button'
CONFIGURATION_SUBMIT_CONFIG_BUTTON = 'configuration.submit_config_button'
CONFIGURATION_DELETE_CONFIG_BUTTON = 'configuration.delete_config_button'
CONFIGURATION_BROWSE_FILES_ENTRY = 'configuration.browse_files_entry'
CONFIGURATION_BROWSE_FILES_BUTTON = 'configuration.browse_files_button'

# AT Configuration (Index 0)
CONFIGURATION_AT_CONFIG_0_ATF_ENTRY = 'configuration.at_config.0.atf_entry'
CONFIGURATION_AT_CONFIG_0_ATK_ENTRY = 'configuration.at_config.0.atk_entry'
CONFIGURATION_AT_CONFIG_0_ATT_ENTRY = 'configuration.at_config.0.att_entry'

# AT Configuration (Index 1)
CONFIGURATION_AT_CONFIG_1_ATF_ENTRY = 'configuration.at_config.1.atf_entry'
CONFIGURATION_AT_CONFIG_1_ATK_ENTRY = 'configuration.at_config.1.atk_entry'
CONFIGURATION_AT_CONFIG_1_ATT_ENTRY = 'configuration.at_config.1.att_entry'

# AT Configuration (Index 2)
CONFIGURATION_AT_CONFIG_2_ATF_ENTRY = 'configuration.at_config.2.atf_entry'
CONFIGURATION_AT_CONFIG_2_ATK_ENTRY = 'configuration.at_config.2.atk_entry'
CONFIGURATION_AT_CONFIG_2_ATT_ENTRY = 'configuration.at_config.2.att_entry'

# AT Configuration (Index 3)
CONFIGURATION_AT_CONFIG_3_ATF_ENTRY = 'configuration.at_config.3.atf_entry'
CONFIGURATION_AT_CONFIG_3_ATK_ENTRY = 'configuration.at_config.3.atk_entry'
CONFIGURATION_AT_CONFIG_3_ATT_ENTRY = 'configuration.at_config.3.att_entry'

# Procedure Controlling constants
PROC_CONTROLLING_PROCEDURE_COMBOBOX = 'proc_controlling.procedure_combobox'
PROC_CONTROLLING_START_BUTTON = 'proc_controlling.start_button'
PROC_CONTROLLING_STOP_BUTTON = 'proc_controlling.stop_button'
PROC_CONTROLLING_RUNNING_PROC_LABEL = 'proc_controlling.running_proc_label'

# Ramp constants
RAMP_F_START = 'Ramp.ramp_f_start.entry_str'
RAMP_F_STOP = 'Ramp.ramp_f_stop.entry_str'
RAMP_F_STEP = 'Ramp.ramp_f_step.entry_str'
RAMP_T_ON_TIME = 'Ramp.ramp_t_on.time_str'
RAMP_T_ON_UNIT = 'Ramp.ramp_t_on.unit_str'
RAMP_T_OFF_TIME = 'Ramp.ramp_t_off.time_str'
RAMP_T_OFF_UNIT = 'Ramp.ramp_t_off.unit_str'

# Measuring constants
MEASURING_TARGET_COMBOBOX = 'measuring.target_combobox'
MEASURING_CAPTURE_BUTTON = 'measuring.capture_button'

# Spectrum Measure constants
SPECTRUM_MEASURE_FREQ_START= 'Spectrum Measure.start.entry'
SPECTRUM_MEASURE_FREQ_STOP = 'Spectrum Measure.stop.entry'
SPECTRUM_MEASURE_STEP_ENTRY = 'Spectrum Measure.step.entry'
SPECTRUM_MEASURE_HOLD_ON_TIME_ENTRY = 'Spectrum Measure.hold_on.time_entry'
SPECTRUM_MEASURE_HOLD_ON_UNIT_BUTTON = 'Spectrum Measure.hold_on.unit_button'
SPECTRUM_MEASURE_HOLD_OFF_TIME_ENTRY = 'Spectrum Measure.hold_off.time_entry'
SPECTRUM_MEASURE_HOLD_OFF_UNIT_BUTTON = 'Spectrum Measure.hold_off.unit_button'

# Message Box constants
MESSAGE_BOX = "MessageBox"
MESSAGE_BOX_MSG = "MessageBox.message"
for option in DialogOptions:
    globals()[f"MESSAGE_BOX_OPTION_{option.name}"] = f"MessageBox.{option.name}"

