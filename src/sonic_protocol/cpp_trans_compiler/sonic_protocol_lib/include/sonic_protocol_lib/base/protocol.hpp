#pragma once
#include <initializer_list>
#include <string_view>
#include <span>
#include <optional>
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
    std::span<const std::optional<CommandDef>> commands;
    std::span<const AnswerDef> answers;
};

}