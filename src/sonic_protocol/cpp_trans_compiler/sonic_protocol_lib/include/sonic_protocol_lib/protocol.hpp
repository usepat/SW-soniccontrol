#pragma once
#include <initializer_list>
#include <string_view>
#include "answer_def.hpp"
#include "command_def.hpp"
#include "enums.hpp"

namespace sonic_protocol_lib {

struct Version {
  uint8_t major{0};
  uint8_t minor{0};
  uint8_t patch{0};
};

struct Protocol {
    Version version;
    DeviceType device;
    bool isRelease;
    std::string_view options;
    std::initializer_list<CommandDef> commands;
    std::initializer_list<AnswerDef> answers;
};

}