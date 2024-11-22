#pragma once
#include <initializer_list>
#include <array>

#include "sonic_protocol_lib/protocol.hpp"

namespace sonic_protocol_lib {

#define FIELD_LIMITS
/**/FIELD_LIMITS/**/ // the python script will replace this

#define PROTOCOL_COUNT {0}
constexpr std::size_t protocol_count() {
    return /**/PROTOCOL_COUNT/**/; // the python script will replace this
}
#undef PROTOCOL_COUNT

// Command counts placeholder
#define COMMAND_COUNT {}
constexpr std::array<std::size_t, protocol_count()> command_counts() {
    return /**/COMMAND_COUNT/**/; // the Python script will replace this
}
#undef COMMAND_COUNT

// Answer counts placeholder
#define ANSWER_COUNT {}
constexpr std::array<std::size_t, protocol_count()> answer_counts() {
    return /**/ANSWER_COUNT/**/; // the Python script will replace this
}
#undef ANSWER_COUNT

#define PROTOCOLS {}
constexpr std::array<Protocol, protocol_count()> protocols() {
    return /**/PROTOCOLS/**/; // the python script will replace this
}
#undef PROTOCOLS

}