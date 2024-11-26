#pragma once
#include <initializer_list>
#include <string_view>
#include <span>
#include "answer_def.hpp"
#include "command_def.hpp"
#include "enums.hpp"

namespace sonic_protocol_lib {

struct Version {
  uint8_t major{0};
  uint8_t minor{0};
  uint8_t patch{0};
};

class Protocol {
public:
    Version version;
    DeviceType device;
    bool isRelease;
    std::string_view options;
    std::span<CommandDef> commands;
    std::span<AnswerDef> answers;
};

}