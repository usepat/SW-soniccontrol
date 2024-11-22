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

}