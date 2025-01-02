#pragma once
#include <cstdint>

namespace sonic_protocol_lib {

#define COMMAND_CODE_MEMBERS 
enum class CommandCode : int16_t  {
    /**/COMMAND_CODE_MEMBERS/**/  // the python script will replace this
};
#undef COMMAND_CODE_MEMBERS 


#define COMMAND_CODE_SWITCH_CASE
inline bool isValidCode(std::uint16_t value) {
    CommandCode code = static_cast<CommandCode>(value);
    switch (code) {
        /**/COMMAND_CODE_SWITCH_CASE/**/
            return true;
        default:
            return false;
    }
}
#undef COMMAND_CODE_SWITCH_CASE


}