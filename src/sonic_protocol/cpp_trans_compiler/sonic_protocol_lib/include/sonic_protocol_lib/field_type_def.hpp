#pragma once
#include <optional>
#include <initializer_list>
#include <cstdint>

#include "si_units.hpp"
#include <etl/array.h>

namespace sonic_protocol_lib {


enum class DataType {
    // Primitive
    UINT8,
    UINT16,
    UINT32,
    FLOAT,
    STRING,
    BOOL,

    // Enum
    E_DEVICE_TYPE,
    E_COMMUNICATION_CHANNEL,
    E_COMMUNICATION_PROTOCOL,
    E_INPUT_SOURCE,
    E_PROCEDURE,

    // Classes
    VERSION,
};

enum class ConverterReference {
    PRIMITIVE,
    ENUM,
    SIGNAL,
    VERSION,
    BUILD_TYPE,
    TERMINATION,
};

constexpr std::size_t MAX_ALLOWED_VALUES = 10;
template <typename T>
struct FieldLimits {
    std::optional<T> min;
    std::optional<T> max;
    std::optional<etl::vector<T, MAX_ALLOWED_VALUES>> allowed_values;
};

struct FieldTypeDef {
    DataType type {DataType::UINT16};
    ConverterReference converter_reference {ConverterReference::PRIMITIVE};
    const void * limits {nullptr}; // should never be null, but we need to initialize it with nullptr, because of undefined behaviour
    std::optional<SIUnit> si_unit {std::nullopt};
    std::optional<SIPrefix> si_prefix {std::nullopt};
};
}