#pragma once
#include <initializer_list>
#include <string_view>
#include <span>
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

class IProtocol {
public:
    virtual ~IProtocol() = default;
    virtual Version getVersion() const = 0;
    virtual DeviceType getDevice() const = 0;
    virtual bool getIsRelease() const = 0;
    virtual std::string_view getOptions() const = 0;
    virtual std::span<const CommandDef> getCommandsSpan() const = 0;
    virtual std::span<const AnswerDef> getAnswersSpan() const = 0;
};

template<size_t CommandCount, size_t AnswerCount>
class ProtocolTemplated : public IProtocol {
private:
  Version version;
  DeviceType device;
  bool isRelease;
  std::string_view options;
  etl::array<CommandDef, CommandCount> commands;
  etl::array<AnswerDef, AnswerCount> answers;
public:
  constexpr ProtocolTemplated(Version ver, DeviceType dev, bool release, std::string_view opts, 
                const etl::array<CommandDef, CommandCount>& cmds, 
                const etl::array<AnswerDef, AnswerCount>& ans)
    : version(ver), device(dev), isRelease(release), options(opts), commands(cmds), answers(ans) {}

  Version getVersion() const override {
    return version;
  }

  DeviceType getDevice() const override {
    return device;
  }

  bool getIsRelease() const override {
    return isRelease;
  }

  std::string_view getOptions() const override {
    return options;
  }

  std::span<const CommandDef> getCommandsSpan() const override {
    return std::span<const CommandDef>(commands.data(), commands.size());
  }

  std::span<const AnswerDef> getAnswersSpan() const override {
    return std::span<const AnswerDef>(answers.data(), answers.size());
  }
};

template<size_t Count>
using Protocol = ProtocolTemplated<Count, Count>;

}