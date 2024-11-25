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

template <size_t CommandCount, size_t AnswerCount>
struct ProtocolData {
    Version version;
    DeviceType device;
    bool isRelease;
    std::string_view options;
    etl::array<CommandDef, CommandCount> commands;
    etl::array<AnswerDef, AnswerCount> answers;
};

template <size_t CommandCount, size_t AnswerCount>
class ProtocolTemplated : public IProtocol {
private:
    ProtocolData<CommandCount, AnswerCount> data;

public:
    constexpr ProtocolTemplated(ProtocolData<CommandCount, AnswerCount> data)
        : data(data) {}

    Version getVersion() const override { return data.version; }
    DeviceType getDevice() const override { return data.device; }
    bool getIsRelease() const override { return data.isRelease; }
    std::string_view getOptions() const override { return data.options; }
    std::span<const CommandDef> getCommandsSpan() const override {
        return std::span<const CommandDef>(data.commands.data(), data.commands.size());
    }
    std::span<const AnswerDef> getAnswersSpan() const override {
        return std::span<const AnswerDef>(data.answers.data(), data.answers.size());
    }
};


template<size_t Count>
using Protocol = ProtocolTemplated<Count, Count>;

}