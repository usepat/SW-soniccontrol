#pragma once
#include <optional>
#include <initializer_list>
#include <cstdint>

#include "si_units.hpp"
#include <span>

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
    E_WAVEFORM,

    // Classes
    VERSION,
    TIMESTAMP
};

inline std::string_view convert_data_type_to_string(DataType value) {
    switch (value) {
        case DataType::UINT8:
            return "uint8";
        case DataType::UINT16:
            return "uint16";
        case DataType::UINT32:
            return "uint32";
        case DataType::FLOAT:
            return "float";
        case DataType::STRING:
            return "string";
        case DataType::BOOL:
            return "bool";
        case DataType::E_DEVICE_TYPE:
            return "e_device_type";
        case DataType::E_COMMUNICATION_CHANNEL:
            return "e_communication_channel";
        case DataType::E_COMMUNICATION_PROTOCOL:
            return "e_communication_protocol";
        case DataType::E_INPUT_SOURCE:
            return "e_input_source";
        case DataType::E_PROCEDURE:
            return "e_procedure";
        case DataType::E_WAVEFORM:
            return "e_waveform";
        case DataType::TIMESTAMP:
            return "timestamp";
        case DataType::VERSION:
            return "version";
        default:
            assert (false);
    }
}

enum class ConverterReference {
    PRIMITIVE,
    ENUM,
    SIGNAL,
    VERSION,
    BUILD_TYPE,
    TERMINATION,
    TIMESTAMP
};

template <typename T>
struct FieldLimits {
    std::optional<T> min;
    std::optional<T> max;
    std::optional<std::span<const T>> allowed_values;
};

struct FieldTypeDef {
    DataType type {DataType::UINT16};
    ConverterReference converter_reference {ConverterReference::PRIMITIVE};
    const void * limits {nullptr}; // should never be null, but we need to initialize it with nullptr, because of undefined behaviour
    std::optional<SIUnit> si_unit {std::nullopt};
    std::optional<SIPrefix> si_prefix {std::nullopt};
};
}