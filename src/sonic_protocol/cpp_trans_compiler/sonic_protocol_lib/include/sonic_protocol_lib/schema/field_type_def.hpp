#pragma once
#include <optional>
#include <initializer_list>
#include <cstdint>

#include "sonic_protocol_lib/schema/si_units.hpp"
#include <span>

namespace sonic_protocol_lib {
    
using EnumValue_t = int16_t;
using TypeDefinitionRef_t = int16_t;


#define BASE_DATA_TYPE enum class BaseDataType : EnumValue_t { UINT32 };
/**
 * @brief describes the base data type
 */
/**/BASE_DATA_TYPE/**/
#undef BASE_DATA_TYPE


/**
 * @brief Is used to reference custom data types like enums created by the custom protocols.
 */

template <typename T>
struct FieldLimits {
    std::optional<T> min;
    std::optional<T> max;
    std::optional<std::span<const T>> allowed_values;
};

struct FieldTypeDef {
    BaseDataType data_type {BaseDataType::UINT32};
    std::optional<TypeDefinitionRef_t> type_def_ref {std::nullopt};
    const void * limits {nullptr}; // should never be null, but we need to initialize it with nullptr, because of undefined behaviour
    std::optional<SIUnit> si_unit {std::nullopt};
    std::optional<SIPrefix> si_prefix {std::nullopt};
};
}