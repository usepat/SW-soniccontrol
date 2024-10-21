#pragma once
#include <optional>
#include <initializer_list>
#include <cstdint>


namespace sonic::protocol_defs {


enum class DataType {
    // Primitive
    INT,
    DOUBLE,
    STRING,
    BOOL,

    // Enum
    E_DEVICE_TYPE,
    E_COMMUNICATION_CHANNEL,
    E_COMMUNICATION_PROTOCOL,
    E_INPUT_SOURCE,

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

enum class SIUnit {
    METER,
    SECOND,
    HERTZ,
    CELSIUS,
    AMPERE,
    VOLTAGE,
    PERCENT,
    DEGREE,
};

enum class SIPrefix {
    NANO,
    MICRO,
    MILLI,
    NONE,
    KILO,
    MEGA,
    GIGA,
};

struct FieldLimits { 
};

template <typename T>
struct FieldLimitsImpl : FieldLimits {
    std::initializer_list<T> allowed_values;
    std::optional<T> min;
    std::optional<T> max;
};

struct FieldTypeDef {
    DataType type {DataType::INT};
    ConverterReference converter_reference {ConverterReference::PRIMITIVE};
    FieldLimits *limits {nullptr}; // should never be null, but we need to initialize it with nullptr, because of undefined behaviour
    std::optional<SIUnit> si_unit {std::nullopt};
    std::optional<SIPrefix> si_prefix {std::nullopt};
};
}