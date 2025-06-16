*** Settings ***

Resource    keywords_remote_control.robot

Suite Setup    Connect to device
Suite Teardown    RemoteController.Disconnect

Test Setup    Reconnect if disconnected

*** Test Cases ***

# Wont work if device is in Debug Mode(because of USB)
Test if device save parameters like freq and gain
    [Documentation]    After restarting parameters should be saved
    [Tags]    expensive_to_run
    [Setup]    RemoteController.Send Command     !sonic_force    
    RemoteController.Send Command     !stop
    [Teardown]    RemoteController.Send Command     !log[global]=ERROR
    Send command and check response    !freq\=1000000   should_be_valid=${True}    ${FIELD_FREQUENCY}=${1000000}
    Send command and check response    !gain\=100   should_be_valid=${True}    ${FIELD_GAIN}=${100}
    RemoteController.Send Command     !restart
    Sleep for 20000 ms
    Reconnect if disconnected
    Send command and check response    ?freq   should_be_valid=${True}    ${FIELD_FREQUENCY}=${1000000}
    Send command and check response    ?gain  should_be_valid=${True}    ${FIELD_GAIN}=${100}  
