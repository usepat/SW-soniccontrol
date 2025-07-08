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

template<typename Protocol>
concept ProtocolConcept = requires {
    // Check nested type aliases
    typename Protocol::CommandCode;
    typename Protocol::FieldName;
    typename Protocol::DataType;

    // Check static constexpr members with correct types
    { Protocol::version } -> std::same_as<const Version&>;
    Protocol::device; // just check if it has device as member
    { Protocol::isRelease } -> std::same_as<const bool&>;
    { Protocol::options } -> std::same_as<const char*>;
} &&
ContainerOf<decltype(Protocol::commands), std::optional<CommandDef>> &&
ContainerOf<decltype(Protocol::answers), AnswerDef>;
    
}
