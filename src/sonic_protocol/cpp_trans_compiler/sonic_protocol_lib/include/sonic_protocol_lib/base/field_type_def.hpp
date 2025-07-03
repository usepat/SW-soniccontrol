#pragma once
#include <optional>
#include <initializer_list>
#include <cstdint>

#include "sonic_protocol_lib/base/si_units.hpp"
#include <span>

namespace sonic_protocol_lib {


using DataType_t = uint16_t;
using EnumValue_t = int32_t;

enum class ConverterReference {
    PRIMITIVE,
    ENUM,
    VERSION,
    TIMESTAMP,
};

template <typename T>
struct FieldLimits {
    std::optional<T> min;
    std::optional<T> max;
    std::optional<std::span<const T>> allowed_values;
};

struct FieldTypeDef {
    DataType_t type {0};
    ConverterReference converter_reference {ConverterReference::PRIMITIVE};
    const void * limits {nullptr}; // should never be null, but we need to initialize it with nullptr, because of undefined behaviour
    std::optional<SIUnit> si_unit {std::nullopt};
    std::optional<SIPrefix> si_prefix {std::nullopt};
};
}