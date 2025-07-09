#pragma once

#include <cstdint>
#include "correspondence/schema/internal_representation.hpp"

namespace sonic_protocol_lib {

constexpr size_t NUM_ANSWER_FIELDS = 16;
using IRObjectAnswer = IRObject<NUM_ANSWER_FIELDS>;

class Answer {
private:
    CommandCode_t code; ///< Represents a unique code identifying the type of answer.
    IRObjectAnswer irObj;

public:
    inline explicit Answer(const CommandCode_t code, const IRObjectAnswer& irObj) 
    : code {code}, irObj {irObj} {}

    virtual ~Answer() = default;

    inline CommandCode_t getCode() const { return code; }
    inline IRObjectAnswer getIRObject() const { return irObj; }

    inline bool is_error() const {
        // codes from 20000 upwards are reserved for errors 
        constexpr int16_t ERROR_CODE_SECTION_BEGIN {20000};
        return static_cast<int16_t>(code) >= ERROR_CODE_SECTION_BEGIN;
    }
};

}