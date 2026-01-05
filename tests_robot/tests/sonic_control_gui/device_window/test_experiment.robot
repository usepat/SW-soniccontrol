*** Settings ***

Resource    ../keywords_gui.robot


*** Variables ***
${UPDATE_INTERVAL}    100

*** Test Cases ***

test experiment control button
    Gui.Switch to tab "${MEASURING_TAB}"

    ${label_control_button }=    Gui.Get text of widget "${MEASURING_CONTROL_BUTTON}"
    Should Be Equal As Strings    ${label_control_button}    ${LABEL_NEW_EXPERIMENT}
    Gui.Press button "${MEASURING_CONTROL_BUTTON}"
    Gui.Let the app update for "${UPDATE_INTERVAL}" ms

    ${label_control_button }=    Gui.Get text of widget "${MEASURING_CONTROL_BUTTON}"
    Should Be Equal As Strings    ${label_control_button}    ${LABEL_FINISH_LABEL}
    Gui.Press button "${MEASURING_CONTROL_BUTTON}"
    Gui.Let the app update for "${UPDATE_INTERVAL}" ms

    ${label_control_button }=    Gui.Get text of widget "${MEASURING_CONTROL_BUTTON}"
    Should Be Equal As Strings    ${label_control_button}    ${LABEL_SELECTED}
    Gui.Set text of widget "${MEASURING_TARGET_COMBOBOX}" to "Free"
    Gui.Press button "${MEASURING_CONTROL_BUTTON}"
    Gui.Let the app update for "${UPDATE_INTERVAL}" ms

    # start experiment
    ${label_control_button }=    Gui.Get text of widget "${MEASURING_CONTROL_BUTTON}"
    Should Be Equal As Strings    ${label_control_button}    ${LABEL_START_CAPTURE}
    Gui.Press button "${MEASURING_CONTROL_BUTTON}"
    Gui.Let the app update for "${UPDATE_INTERVAL}" ms
    
    ${label_control_button }=    Gui.Get text of widget "${MEASURING_CONTROL_BUTTON}"
    Should Be Equal As Strings    ${label_control_button}    ${LABEL_END_CAPTURE}
    Gui.Press button "${MEASURING_CONTROL_BUTTON}" 
    Gui.Let the app update for "${UPDATE_INTERVAL}" ms

    ${label_control_button }=    Gui.Get text of widget "${MEASURING_CONTROL_BUTTON}" 
    Should Be Equal As Strings    ${label_control_button}    ${LABEL_NEW_EXPERIMENT}


experiment capture ends if procedure finishes
    Start ramp capture

    Let the app update for "2000" ms

    # stop procedure
    Gui.Set text of widget "${SERIAL_MONITOR_COMMAND_LINE_INPUT_ENTRY}" to "!stop"
    Gui.Press button "${SERIAL_MONITOR_SEND_BUTTON}"    

    ${label_control_button }=    Gui.Wait up to "2000" ms for the widget "${MEASURING_CONTROL_BUTTON}" to change text  
    Should Be Equal As Strings    ${label_control_button}    ${LABEL_NEW_EXPERIMENT}


procedure stops if capture ends
    Start ramp capture

    Let the app update for "2000" ms

    # stop experiment
    Gui.Press button "${MEASURING_CONTROL_BUTTON}"
    
    ${label_control_button }=    Gui.Wait up to "2000" ms for the widget "${MEASURING_CONTROL_BUTTON}" to change text  
    ${proc_label }=    Gui.Get text of widget "${STATUS_BAR_PROCEDURE_LABEL}"  

    Should Be Equal As Strings    ${label_control_button}    ${LABEL_NEW_EXPERIMENT}
    Should Contain   ${proc_label}    none


experiment capture ends if spectrum measure finishes
    Start spectrum measure capture     # runs approximately 6000 ms

    ${label_control_button }=    Gui.Wait up to "10000" ms for the widget "${MEASURING_CONTROL_BUTTON}" to change text  
    Should Be Equal As Strings    ${label_control_button}    ${LABEL_NEW_EXPERIMENT}


spectrum measure stops if capture ends
    Start spectrum measure capture  

    Let the app update for "2000" ms

    # stop experiment
    Gui.Press button "${MEASURING_CONTROL_BUTTON}"
    
    ${label_control_button }=    Gui.Wait up to "2000" ms for the widget "${MEASURING_CONTROL_BUTTON}" to change text  
    Should Be Equal As Strings    ${label_control_button}    ${LABEL_NEW_EXPERIMENT}

    Let the app update for "2000" ms

    # check if spectrum  measure stopped by checking if frequency changes over time
    ${label_freq1}=    Gui.Get text of widget "${STATUS_BAR_FREQ_LABEL}"
    Let the app update for "5000" ms
    ${label_freq2}=    Gui.Get text of widget "${STATUS_BAR_FREQ_LABEL}"
    Should Be Equal As Strings    ${label_freq1}    ${label_freq2}


*** Keywords ***

Start ramp capture
    Gui.Switch to tab "${MEASURING_TAB}"
    Gui.Switch to tab "${PROCEDURES_TAB}"

    # Start new experiment
    Gui.Press button "${MEASURING_CONTROL_BUTTON}" 
    # finish template
    Gui.Press button "${MEASURING_CONTROL_BUTTON}"
    # select target
    Gui.Set text of widget "${MEASURING_TARGET_COMBOBOX}" to "Procedure"
    Gui.Press button "${MEASURING_CONTROL_BUTTON}"

    # start experiment
    Set ramp args
    Gui.Press button "${MEASURING_CONTROL_BUTTON}"

    ${proc_label}=    Gui.Wait up to "10000" ms for the widget "${STATUS_BAR_PROCEDURE_LABEL}" to change text
    Should Contain   ${proc_label}    ramp

    ${label_control_button }=    Gui.Get text of widget "${MEASURING_CONTROL_BUTTON}"
    Should Be Equal As Strings    ${label_control_button}    ${LABEL_END_CAPTURE}

    
Start spectrum measure capture
    Gui.Switch to tab "${MEASURING_TAB}"
    Gui.Switch to tab "${SPECTRUM_MEASURE_TAB}"

    # Start new experiment
    Gui.Press button "${MEASURING_CONTROL_BUTTON}" 
    # finish template
    Gui.Press button "${MEASURING_CONTROL_BUTTON}"
    # select target
    Gui.Set text of widget "${MEASURING_TARGET_COMBOBOX}" to "Spectrum Measure"
    Gui.Press button "${MEASURING_CONTROL_BUTTON}"

    # start capture
    Set spectrum measure args
    Gui.Press button "${MEASURING_CONTROL_BUTTON}"

    # spectrum measure started if freq changed
    Gui.Wait up to "10000" ms for the widget "${STATUS_BAR_FREQ_LABEL}" to change text

    ${label_control_button }=    Gui.Get text of widget "${MEASURING_CONTROL_BUTTON}"
    Should Be Equal As Strings    ${label_control_button}    ${LABEL_END_CAPTURE}
