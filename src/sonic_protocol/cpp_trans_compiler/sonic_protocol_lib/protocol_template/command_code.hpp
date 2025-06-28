#pragma once
#include <cstdint>

namespace sonic_protocol_lib {

#define COMMAND_CODE_NAME

#define COMMAND_CODE_MEMBERS 
enum class /**/COMMAND_CODE_NAME/**/ : int16_t  {
    /**/COMMAND_CODE_MEMBERS/**/  // the python script will replace this
};
#undef COMMAND_CODE_MEMBERS 

namespace{
    using CommandCode = /**/COMMAND_CODE_NAME/**/;
}

#define COMMAND_CODE_SWITCH_CASE
inline bool isValidCode(std::uint16_t value) {
    /**/COMMAND_CODE_NAME/**/ code = static_cast</**/COMMAND_CODE_NAME/**/>(value);
    switch (code) {
        /**/COMMAND_CODE_SWITCH_CASE/**/
            return true;
        default:
            return false;
    }
}
#undef COMMAND_CODE_SWITCH_CASE


}