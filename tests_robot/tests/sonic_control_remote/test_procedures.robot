*** Settings ***

Resource    keywords_remote_control.robot

Suite Setup    Connect to device
Suite Teardown    RemoteController.Disconnect

Test Setup    Setup Procedure Test
Test Teardown    RemoteController.Send Command    !stop

Test Tags    -descale

*** Test Cases ***

Check procedure command returns error, if ramp_f_start and ramp_f_stop are the same
    Send Command And Check Response    !ramp_f_start\=${100100}
    Send Command And Check Response    !ramp_f_stop\=${100100}
    Send command and check response    !ramp    ${False}

Check setter commands get blocked during procedure run
    ${EXPECTED_PROCEDURE}=    Convert to procedure    RAMP
    # TODO set ramp args before
    Send command and check response    !ramp    ${FIELD_PROCEDURE}=${EXPECTED_PROCEDURE}
    Sleep    1000ms
    Send command and check response    !freq\=100000    ${False}

Check getter commands are allowed during procedure run
    ${EXPECTED_PROCEDURE}=    Convert to procedure    RAMP
    # TODO set ramp args before
    Send command and check response    !ramp    ${FIELD_PROCEDURE}=${EXPECTED_PROCEDURE}
    Sleep    1000ms
    Send command and check response    ?freq    ${True}

Test Stop turns off procedure
    ${EXPECTED_PROCEDURE}=    Convert to procedure    RAMP
    # TODO set ramp args before
    Send command and check response    !ramp    ${FIELD_PROCEDURE}=${EXPECTED_PROCEDURE}
    Sleep    1000ms
    ${EXPECTED_PROCEDURE}=    Convert to procedure    NO_PROC
    Send command and check response    !stop    ${True}    ${FIELD_PROCEDURE}=${EXPECTED_PROCEDURE}

Test if ramp does not crash
    [Setup]    RemoteController.Send Command     !log[procedureLogger]=DEBUG
    [Teardown]    RemoteController.Send Command     !log[procedureLogger]=ERROR
    RemoteController.Send Command     !ramp
    Sleep for 10000 ms
    Send command and check if the device crashes    !stop

Test if after ramp signal is off
    [Setup]    RemoteController.Send Command     !log[procedureLogger]=DEBUG
    [Teardown]    RemoteController.Send Command     !log[procedureLogger]=ERROR
    Set Ramp Args
    RemoteController.Send Command     !ramp
    Sleep for 15000 ms
    ${EXPECTED_PROCEDURE}=    Convert to procedure    NO_PROC
    Send command and check response    -    ${FIELD_PROCEDURE}=${EXPECTED_PROCEDURE}

Test if tune notifies or halts
    [Setup]     Set Tune Args
    [Teardown]    RemoteController.Send Command    !stop
    RemoteController.Send Command     !tune
    # TODO check if tune send notification or send procedure halted


*** Keywords ***

Setup Procedure Test
    Reconnect if disconnected
    Set Ramp Args

Set Ramp Args
    [Arguments]    ${f_start}=100000    ${f_stop}=150000    ${f_step}=10000    ${t_on}=2000    ${t_off}=0
    Send Command And Check Response    !ramp_f_start\=${f_start}
    Send Command And Check Response    !ramp_f_stop\=${f_stop}
    Send Command And Check Response    !ramp_f_step\=${f_step}
    Send Command And Check Response    !ramp_t_on\=${t_on}
    Send Command And Check Response    !ramp_t_off\=${t_off} 


Set Tune Args
    [Arguments]    ${t_time}=5000    ${t_step}=200    ${f_shift}=0    ${n_steps}=4    ${f_step}=1000    ${gain}=100
    Send Command And Check Response    !tune_t_time\=${t_time}
    Send Command And Check Response    !tune_t_step\=${t_step}
    Send Command And Check Response    !tune_f_shift\=${f_shift}
    Send Command And Check Response    !tune_n_steps\=${n_steps}
    Send Command And Check Response    !tune_f_step\=${f_step}
    Send Command And Check Response    !tune_gain\=${gain}