*** Settings ***

Resource    ../keywords_gui.robot

Test Teardown    Set procedure tab to default state


*** Variables ***


*** Test Cases ***

Run ramp procedure
    Gui.Switch to tab "${PROCEDURES_TAB}"
    Gui.Set text of widget "${PROC_CONTROLLING_PROCEDURE_COMBOBOX}" to "Ramp"
    Gui.Set text of widget "${RAMP_F_START}" to "100000"
    Gui.Set text of widget "${RAMP_F_STOP}" to "200000"
    Gui.Set text of widget "${RAMP_F_STEP}" to "10000"
    Gui.Set text of widget "${RAMP_T_ON_TIME}" to "500"
    Gui.Set text of widget "${RAMP_T_ON_UNIT}" to "ms"
    Gui.Set text of widget "${RAMP_T_OFF_TIME}" to "500"
    Gui.Set text of widget "${RAMP_T_OFF_UNIT}" to "ms"
    Gui.Press button "${PROC_CONTROLLING_START_BUTTON}"

    Gui.Wait up to "200" ms for the widget "${MESSAGE_BOX}" to be registered
    Gui.Press button "${MESSAGE_BOX_OPTION_PROCEED}"
    
    Gui.Wait up to "10000" ms for the widget "${STATUS_BAR_PROCEDURE_LABEL}" to change text

    # We need to wait more than 500 ms. Else we get issues with timing
    FOR    ${i}    IN RANGE    10
        ${signal_label}=    Gui.Wait up to "700" ms for the widget "${STATUS_BAR_SIGNAL_LABEL}" to change text
        Should Contain    ${signal_label}    ON

        ${signal_label}=    Gui.Wait up to "700" ms for the widget "${STATUS_BAR_SIGNAL_LABEL}" to change text
        Should Contain    ${signal_label}    OFF
    END

    ${proc_running_label}=    Gui.Wait up to "700" ms for the widget "${PROC_CONTROLLING_RUNNING_PROC_LABEL}" to change text
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
