#pragma once
#include <initializer_list>
#include <array>
#include "answer_def.hpp"
#include "command_def.hpp"

namespace sonic_protocol_lib {

template <std::size_t CommandCount, std::size_t AnswerCount>
struct Protocol {
    std::array<CommandDef, CommandCount> commands;
    std::array<AnswerDef, AnswerCount> answers;
};

}