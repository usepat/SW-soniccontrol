#pragma once

#include <array>
#include <cstdint>
#include <string_view>
#include <span>
#include <optional>
#include <concepts>

#include "sonic_protocol_lib/schema/answer_def.hpp"
#include "sonic_protocol_lib/schema/code.hpp"
#include "sonic_protocol_lib/schema/command_def.hpp"

namespace sonic_protocol_lib {


template<typename C, typename T>
concept ContainerOf = 
    std::ranges::range<C> &&                             // is iterable
    std::same_as<std::ranges::range_value_t<C>, T>;

struct Version {
    uint8_t major{0};
    uint8_t minor{0};
    uint8_t patch{0};
};

#define DEVICE_TYPE enum class DeviceType : EnumValue_t { MVP_WORKER, DESCALE };
/**/DEVICE_TYPE/**/
#undef DEVICE_TYPE

#define BUILD_TYPE enum class BuildType : EnumValue_t { RELEASE, DEBUG };
/**/BUILD_TYPE/**/
#undef BUILD_TYPE

struct ProtocolDescriptor {
    Version version;
    DeviceType device_type {DeviceType::MVP_WORKER};
    BuildType build_type {BuildType::RELEASE};
    etl::string_view options {""};
};

template<typename Protocol>
concept ProtocolConcept = requires {
    // Check nested type aliases
    typename Protocol::CommandCode;
    typename Protocol::FieldName;
    typename Protocol::DataType;

    // Check static constexpr members with correct types
    { Protocol::descriptor } -> std::same_as<const ProtocolDescriptor&>;
} &&
ContainerOf<decltype(Protocol::commands), std::optional<CommandDef>> &&
ContainerOf<decltype(Protocol::answers), AnswerDef>;
    
}
