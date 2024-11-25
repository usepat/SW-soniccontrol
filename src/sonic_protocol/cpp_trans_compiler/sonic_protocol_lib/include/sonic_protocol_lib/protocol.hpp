#pragma once
#include <initializer_list>
#include <string_view>
#include "answer_def.hpp"
#include "command_def.hpp"
#include "enums.hpp"
#include "etl/vector.h"

namespace sonic_protocol_lib {

struct Version {
  uint8_t major{0};
  uint8_t minor{0};
  uint8_t patch{0};
};

// Placeholder values; these will be overridden by generated_protocol.hpp
constexpr uint8_t MAX_COMMAND_COUNT = 60;
struct Protocol {
    Version version;
    DeviceType device;
    bool isRelease;
    std::string_view options;
    etl::vector<CommandDef, MAX_COMMAND_COUNT> commands;
    etl::vector<AnswerDef, MAX_COMMAND_COUNT> answers;
    uint16_t commandCount;
};


}