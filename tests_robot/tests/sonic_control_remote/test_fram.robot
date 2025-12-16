*** Settings ***

Resource    keywords_remote_control.robot

Suite Setup    Connect to device
Suite Teardown    RemoteController.Disconnect

Test Setup    Reconnect if disconnected

*** Test Cases ***

# Wont work if device is in Debug Mode(because of USB)
Test if device save parameters like freq and gain
    [Documentation]    After restarting parameters should be saved
    [Setup]    Send Command     !sonic_force    
    Send Command     !stop
    [Teardown]    Send Command     !log[global]=ERROR
    Send command and check response    !freq\=123456   should_be_valid=${True}    ${FIELD_FREQUENCY}=${123456}
    Send command and check response    !gain\=100   should_be_valid=${True}    ${FIELD_GAIN}=${100}
    RemoteController.Disconnect
    ${is_connected}=    RemoteController.Is connected to device
    Should Not Be True    ${is_connected}    # just to be 100% sure
    Reconnect if disconnected
    Send command and check response    ?freq   should_be_valid=${True}    ${FIELD_FREQUENCY}=${123456}
    Send command and check response    ?gain  should_be_valid=${True}    ${FIELD_GAIN}=${100}  
