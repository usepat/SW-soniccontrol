#pragma once
#include <initializer_list>
#include <string_view>
#include <span>
#include "sonic_protocol_lib/base/param_def.hpp"
#include "sonic_protocol_lib/base/code.hpp"

namespace sonic_protocol_lib {

struct CommandDef {
    CommandCode_t code {0};
    std::span<const std::string_view> string_identifiers;
    std::span<const ParamDef> params;
};

}