#pragma once
#include <initializer_list>
#include <string_view>
#include "param_def.hpp"
#include "command_code.hpp"

namespace sonic_protocol_lib {

struct CommandDef {
    CommandCode code;
    std::initializer_list<std::string_view> string_identifiers;
    std::initializer_list<ParamDef> params;  
};

}