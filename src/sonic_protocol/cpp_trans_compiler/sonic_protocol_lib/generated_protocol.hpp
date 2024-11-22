#pragma once
#include <initializer_list>
#include <array>
#include <cstdint>

#include "sonic_protocol_lib/protocol.hpp"

namespace sonic_protocol_lib {

#define FIELD_LIMITS
/**/FIELD_LIMITS/**/ // the python script will replace this

#define PROTOCOL_COUNT 0
consteval std::size_t protocol_count() {
    return /**/PROTOCOL_COUNT/**/; // the python script will replace this
}
#undef PROTOCOL_COUNT

#define MAX_COMMAND_COUNT 0
constexpr uint16_t COMMAND_COUNT = /**/MAX_COMMAND_COUNT/**/; // the python script will replace this
#undef MAX_COMMAND_COUNT

struct Protocol : public Protocol_Template<COMMAND_COUNT> {
    using Protocol_Template<COMMAND_COUNT>::Protocol_Template; // Inherit constructors if needed
};

#define PROTOCOLS {}
consteval std::array<Protocol, protocol_count()> protocols() {
    return /**/PROTOCOLS/**/; // the python script will replace this
}
#undef PROTOCOLS


}