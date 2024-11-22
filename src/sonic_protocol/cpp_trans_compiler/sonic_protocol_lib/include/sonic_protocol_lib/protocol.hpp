#pragma once
#include <initializer_list>
#include <string_view>
#include "answer_def.hpp"
#include "command_def.hpp"
#include "enums.hpp"
#include "etl/array.h"

namespace sonic_protocol_lib {

struct Version {
  uint8_t major{0};
  uint8_t minor{0};
  uint8_t patch{0};
};

// Placeholder values; these will be overridden by generated_protocol.hpp
constexpr std::size_t DefaultCommandCount = 1; // Placeholder size
struct Protocol {
    Version version;
    DeviceType device;
    bool isRelease;
    std::string_view options;
    etl::array<CommandDef, DefaultCommandCount> commands;
    etl::array<AnswerDef, DefaultCommandCount> answers;
    uint16_t commandCount;
};


}