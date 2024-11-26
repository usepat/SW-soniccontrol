#pragma once
#include <initializer_list>
#include <array>
#include <cstdint>

#include "sonic_protocol_lib/protocol.hpp"
#include "etl/array.h"

namespace sonic_protocol_lib {

#define FIELD_LIMITS
/**/FIELD_LIMITS/**/ // the python script will replace this
#undef FIELD_LIMITS

#define PROTOCOL_COUNT 0
consteval std::size_t protocol_count() {
    return /**/PROTOCOL_COUNT/**/; // the python script will replace this
}
#undef PROTOCOL_COUNT

#define ALLOWED_VALUES
/**/ALLOWED_VALUES/**/ // the python script will replace this
#undef ALLOWED_VALUES

#define FIELD_DEFS
/**/FIELD_DEFS/**/ // the python script will replace this
#undef FIELD_DEFS

#define PARAM_DEFS
/**/PARAM_DEFS/**/ // the python script will replace this
#undef PARAM_DEFS

#define COMMAND_DEFS
inline constexpr std::array<ParamDef, 0> EMPTY_PARAMS{};/**/COMMAND_DEFS/**/ // the python script will replace this
#undef COMMAND_DEFS

#define ANSWER_DEFS
/**/ANSWER_DEFS/**/ // the python script will replace this
#undef ANSWER_DEFS

#define PROTOCOL_INSTANCES
constexpr std::array<Protocol, protocol_count()> protocol_instances = {
/**/PROTOCOL_INSTANCES/**/ // the python script will replace this
};
#undef PROTOCOL_INSTANCES

consteval std::span<const Protocol> protocols() {
    return protocol_instances;
}


}