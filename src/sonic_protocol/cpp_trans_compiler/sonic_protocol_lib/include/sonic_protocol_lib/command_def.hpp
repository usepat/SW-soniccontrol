#pragma once
#include <initializer_list>
#include <string_view>
#include "param_def.hpp"
#include "command_code.hpp"
#include <etl/vector.h>

namespace sonic_protocol_lib {

constexpr std::size_t MAX_PARAMS = 20;
constexpr std::size_t MAX_STRING_IDENTIFIERS = 10;
struct CommandDef {
    CommandCode code{CommandCode::INVALID};
    etl::vector<std::string_view, MAX_STRING_IDENTIFIERS> string_identifiers;
    etl::vector<ParamDef, MAX_PARAMS> params;
};

}s