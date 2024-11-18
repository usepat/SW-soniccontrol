#pragma once
#include <optional>
#include <initializer_list>
#include <cstdint>

#include "si_units.hpp"

namespace sonic_protocol_lib {


enum class DataType {
    // Primitive
    INT,
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
};

template <typename T>
struct FieldLimits {
    std::optional<T> min;
    std::optional<T> max;
    std::optional<std::initializer_list<T>> allowed_values;
};

struct FieldTypeDef {
    DataType type {DataType::INT};
    ConverterReference converter_reference {ConverterReference::PRIMITIVE};
    const void * limits {nullptr}; // should never be null, but we need to initialize it with nullptr, because of undefined behaviour
    std::optional<SIUnit> si_unit {std::nullopt};
    std::optional<SIPrefix> si_prefix {std::nullopt};
};
}