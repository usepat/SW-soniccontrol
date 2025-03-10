*** Settings ***

Resource    keywords_remote_control.robot

Suite Setup    Connect to device
Suite Teardown    RemoteController.Disconnect

Test Setup    Reconnect if disconnected

*** Test Cases ***

Test if device can handle high throughput and bursts
    [Documentation]    The device cuts off message strings, if an overflow in the serial buffer occurs.
    [Tags]    expensive_to_run
    [Setup]    RemoteController.Send Command     !log[global]=DEBUG
    [Teardown]    RemoteController.Send Command     !log[global]=ERROR
    FOR    ${i}    IN RANGE    0    30
        # TODO: refactor this to use an echo command and send long strings. Could also be an own test
        Send command and check response    !ramp_f_start\=100000    should_be_valid=${True}    ${FIELD_RAMP_F_START}=${100000}
    END 
