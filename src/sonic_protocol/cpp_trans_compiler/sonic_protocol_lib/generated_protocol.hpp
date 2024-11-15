#pragma once
#include <initializer_list>
#include <array>

#include "sonic_protocol_lib/protocol.hpp"

namespace sonic_protocol_lib {

#define FIELD_LIMITS
/**/FIELD_LIMITS/**/ // the python script will replace this

constexpr std::size_t protocol_count() {
    constexpr auto PROTOCOL_COUNT {0}; // default value
    return /**/PROTOCOL_COUNT/**/; // the python script will replace this
}

constexpr std::array<Protocol, protocol_count()> protocols() {
    constexpr  std::array<Protocol, protocol_count()> PROTOCOLS {}; // default value
    return /**/PROTOCOLS/**/; // the python script will replace this
}

}