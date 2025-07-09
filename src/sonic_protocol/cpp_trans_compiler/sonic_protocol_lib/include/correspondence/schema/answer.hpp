#pragma once

#include <cstdint>
#include "correspondence/schema/internal_representation.hpp"

namespace sonic_protocol_lib {

constexpr size_t NUM_ANSWER_FIELDS = 16;
using IRObjectAnswer = IRObject<NUM_ANSWER_FIELDS>;

class BaseAnswer {
private:
    CommandCode_t code; ///< Represents a unique code identifying the type of answer.
    IRObjectAnswer irObj;
    /**
     * @brief Constructs an BaseAnswer object with a specified code.
     *
     * This constructor explicitly requires a CommandCode value during
     * initialization, ensuring that every derived BaseAnswer object is associated
     * with a specific code. Derived classes utilize this constructor in their own
     * constructors, guaranteeing that every Answer instance is initialized with a
     * code.
     *
     * @param c The specific code type that the BaseAnswer object represents.
     */
public:
    inline explicit BaseAnswer(const CommandCode_t code, const IRObjectAnswer& irObj) 
    : code {code}, irObj {irObj} {}
    /// Virtual destructor to ensure proper cleanup in derived classes.
    virtual ~BaseAnswer() = default;

    inline CommandCode_t getCode() const { return code; }
    inline IRObjectAnswer getIRObject() const { return irObj; }

    inline bool is_error() const {
        // codes from 20000 upwards are reserved for errors 
        constexpr int16_t ERROR_CODE_SECTION_BEGIN {20000};
        return static_cast<int16_t>(code) >= ERROR_CODE_SECTION_BEGIN;
    }
};

}