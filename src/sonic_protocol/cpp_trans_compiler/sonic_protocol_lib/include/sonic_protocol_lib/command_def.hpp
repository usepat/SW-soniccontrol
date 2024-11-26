#pragma once
#include <initializer_list>
#include <string_view>
#include "param_def.hpp"
#include "command_code.hpp"

namespace sonic_protocol_lib {

constexpr std::size_t MAX_PARAMS = 20;
constexpr std::size_t MAX_STRING_IDENTIFIERS = 10;
struct CommandDef {
    CommandCode code{CommandCode::INVALID};
    std::span<const std::string_view> string_identifiers;
    std::span<const ParamDef> params;
};

}