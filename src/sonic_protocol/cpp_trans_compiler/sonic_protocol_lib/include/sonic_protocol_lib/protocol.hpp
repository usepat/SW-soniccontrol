#pragma once
#include <initializer_list>
#include <string_view>
#include "answer_def.hpp"
#include "command_def.hpp"
#include "enums.hpp"
#include "etl/span.h" // Include etl::span

namespace sonic_protocol_lib {

struct Version {
  uint8_t major{0};
  uint8_t minor{0};
  uint8_t patch{0};
};

// Placeholder values; these will be overridden by generated_protocol.hpp
struct Protocol {
    Version version;
    DeviceType device;
    bool isRelease;
    std::string_view options;
    etl::span<const CommandDef> commands;
    etl::span<const AnswerDef> answers;
    uint16_t commandCount;
};


}