*** Settings ***

Resource    ../keywords_gui.robot

Test Teardown    Set procedure tab to default state


*** Variables ***


*** Test Cases ***

Run ramp procedure
    Gui.Switch to tab "${PROCEDURES_TAB}"
    Set ramp args
    Gui.Press button "${PROC_CONTROLLING_START_BUTTON}"

    Gui.Wait up to "200" ms for the widget "${MESSAGE_BOX}" to be registered
    Gui.Press button "${MESSAGE_BOX_OPTION_PROCEED}"
    
    Gui.Wait up to "10000" ms for the widget "${STATUS_BAR_PROCEDURE_LABEL}" to change text
    
    ${timeout}=    Set Variable    1500
    # We need to wait more than 1000 ms. Else we get issues with timing
    # We also cannot wait for the signal to change to "on" at the beginning, 
    # because it is more or less simultaneously set with selected proc.
    ${signal_label}=    Gui.Get text of widget "${STATUS_BAR_SIGNAL_LABEL}"
    Should Contain    ${signal_label}    on

    ${signal_label}=    Gui.Wait up to "${timeout}" ms for the widget "${STATUS_BAR_SIGNAL_LABEL}" to change text
    Should Contain    ${signal_label}    off
    
    # Ramp has 10 + 1 step. start and stop freq is included as steps. 
    FOR    ${i}    IN RANGE    10
        ${signal_label}=    Gui.Wait up to "${timeout}" ms for the widget "${STATUS_BAR_SIGNAL_LABEL}" to change text
        Should Contain    ${signal_label}    on

        ${signal_label}=    Gui.Wait up to "${timeout}" ms for the widget "${STATUS_BAR_SIGNAL_LABEL}" to change text
        Should Contain    ${signal_label}    off
    END

    ${proc_running_label}=    Gui.Wait up to "${timeout}" ms for the widget "${PROC_CONTROLLING_RUNNING_PROC_LABEL}" to change text
    Should Be Equal As Strings    ${proc_running_label}    ${LABEL_PROC_NOT_RUNNING}


Stop ramp procedure
    Gui.Switch to tab "${PROCEDURES_TAB}"
    Set ramp args
    Gui.Press button "${PROC_CONTROLLING_START_BUTTON}"

    Gui.Wait up to "200" ms for the widget "${MESSAGE_BOX}" to be registered
    Gui.Press button "${MESSAGE_BOX_OPTION_PROCEED}"
    
    Gui.Wait up to "10000" ms for the widget "${STATUS_BAR_PROCEDURE_LABEL}" to change text

    Gui.Press button "${PROC_CONTROLLING_STOP_BUTTON}"

    ${proc_running_label}=    Gui.Wait up to "2000" ms for the widget "${PROC_CONTROLLING_RUNNING_PROC_LABEL}" to change text
    Should Be Equal As Strings    ${proc_running_label}    ${LABEL_PROC_NOT_RUNNING}


*** Keywords ***

Set procedure tab to default state
    ${label_running}=    Gui.Get text of widget "${PROC_CONTROLLING_RUNNING_PROC_LABEL}"
    IF    '${LABEL_PROC_NOT_RUNNING}' != '${label_running}'
        Gui.Press button "${PROC_CONTROLLING_STOP_BUTTON}"
        Gui.Let the app update for "200" ms
    END
    Gui.Set text of widget "${PROC_CONTROLLING_PROCEDURE_COMBOBOX}" to "Ramp"
    Set device to default state
