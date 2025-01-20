*** Settings ***

Resource    keywords_remote_control.robot

Keyword Tags    descaler    -worker

*** Variables ***

${MIN_SWF}    ${0}
${MAX_SWF}    ${15}


*** Test Cases ***

Test if swf set by setter can be retrieved with getter
    [Tags]    descaler    -worker
    Send Command And Check Response    !swf\=${MIN_SWF}
    Send Command And Check Response    ?swf    ${FIELD_SWF}=${MIN_SWF}
    Send Command And Check Response    !swf\=${MAX_SWF}
    Send Command And Check Response    ?swf    ${FIELD_SWF}=${MAX_SWF}

Test if input source can be set, if analog is set
    [Tags]    descaler    -worker    
    [Teardown]    Reconnect
    ${EXPECTED_INPUT_SOURCE}=    Convert to input source    ANALOG
    Send command and check response    !input_source\=analog    ${FIELD_INPUT_SOURCE}=${EXPECTED_INPUT_SOURCE}
    ${EXPECTED_INPUT_SOURCE}=    Convert to input source    EXTERNAL
    Send command and check response    !input_source\=external    ${FIELD_INPUT_SOURCE}=${EXPECTED_INPUT_SOURCE}