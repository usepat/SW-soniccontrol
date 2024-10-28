#pragma once
#include <initializer_list>
#include <array>
#include "answer_def.hpp"
#include "command_def.hpp"

namespace sonic_protocol_lib {

struct Protocol {
    std::initializer_list<CommandDef> commands;
    std::initializer_list<AnswerDef> answers;
};

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