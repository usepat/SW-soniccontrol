#pragma once
#include <initializer_list>
#include <string_view>
#include "param_def.hpp"
#include "command_code.hpp"

namespace sonic_protocol_lib {

struct CommandDef {
    CommandCode code{CommandCode::E_COMMAND_INVALID};
    std::span<const std::string_view> string_identifiers;
    std::span<const ParamDef> params;
};

}