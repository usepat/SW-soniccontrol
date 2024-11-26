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

#define COMMAND_DEFS
/**/COMMAND_DEFS/**/ // the python script will replace this
#undef COMMAND_DEFS

#define ANSWER_CONTRACTS
/**/ANSWER_CONTRACTS/**/ // the python script will replace this
#undef ANSWER_CONTRACTS

#define PROTOCOL_INSTANCES
/**/PROTOCOL_INSTANCES/**/ // the python script will replace this
#undef PROTOCOL_INSTANCES

#define PROTOCOLS {}
consteval std::array<const IProtocol*, protocol_count()> protocols() {
    /**/PROTOCOLS/**/; // the python script will replace this
}
#undef PROTOCOLS


}