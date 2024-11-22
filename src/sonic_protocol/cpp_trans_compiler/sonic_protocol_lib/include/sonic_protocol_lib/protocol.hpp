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

template <size_t COMMAND_COUNT>
struct Protocol {
    Version version;
    DeviceType device;
    bool isRelease;
    std::string_view options;
    etl::array<CommandDef, COMMAND_COUNT> commands;
    etl::array<AnswerDef, COMMAND_COUNT> answers;
};

}