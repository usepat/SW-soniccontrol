import asyncio
import json
import logging
import re
import sys
import time
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Iterable,
    List,
    Literal,
    Optional,
    Union,
)

import attrs
from icecream import ic
from soniccontrol.communication.communicator import Communicator
from soniccontrol.system import PLATFORM

parrot_feeder = logging.getLogger("parrot_feeder")


# TODO: delete this whole file

@attrs.define
class LegacyConverter:
    worker: Callable[[Any], Any] = attrs.field()
    _converted: bool = attrs.field(default=False, init=False, repr=False)
    _result: Any = attrs.field(init=False)

    @property
    def result(self) -> Any:
        if self._converted:
            return self._result
        else:
            ic("ERROR: Converter did not convert yet.")
            return False

    def convert(self, *args, **kwargs) -> Any:
        try:
            self._result = self.worker(*args, **kwargs)
        except Exception:
            ic("ERROR", sys.exc_info())
            return False
        else:
            self._converted = True
            return self._result


@attrs.define
class LegacyAnswerValidator:
    pattern: str = attrs.field()
    _converters: Dict[str, LegacyConverter] = attrs.field(converter=dict, repr=False)
    _after_converters: Dict[
        str, Dict[Literal["worker", "keywords"], Union[LegacyConverter, str]]
    ] = attrs.field(repr=False)
    _result: Dict[str, Any] = attrs.field(init=False, factory=dict, repr=False)
    _compiled_pattern: re.Pattern[str] = attrs.field(init=False, repr=False)

    def __init__(
        self,
        pattern: str,
        **kwargs: type[Any] | Callable[[Any], Any] | dict[str, Any],
    ) -> None:
        """
        Initializes the CommandValidator instance with the specified pattern and converters.

        Parameters:
            pattern (str): The pattern to be used.
            **kwargs:   Additional keyword arguments that are passed to the Converter constructor.
                        The keyword argument should be a string that is the name of the
                        value. The value should be a Callable that takes in the value and returns
                        the value in the correct type. The converted values are available in the
                        result attribute.

                        Additionally, the keyword argument can be a dictionary with the following
                        keys: "worker" and "keywords". The "worker" key should be a Callable that
                        takes in the value and returns the value in the correct type. The "keywords"
                        are the names of the values used to determine the type of the value. These
                        are "after converters". They are using the previously converted values.

        Example:
            CommandValidator(
                pattern="(?P<foo>[a-z]+) (?P<bar>[0-9]+)",
                foo=int,
                bar=float,
                foobar={
                    "worker": lambda foo, bar: foo * bar,
                    "keywords": ["foo", "bar"],
                }

        Returns:
            None
        """
        workers: dict[str, Callable[[Any], Any]] = dict()
        after_workers: dict[str, Callable[[Any], Any]] = dict()

        for keyword, worker in kwargs.items():
            if isinstance(worker, dict):
                worker["worker"] = LegacyConverter(worker["worker"])
                after_workers[keyword] = worker
                continue
            workers[keyword] = LegacyConverter(worker)

        self.__attrs_init__(
            pattern=pattern,
            converters=workers,
            after_converters=after_workers,
        )

    def __attrs_post_init__(self) -> None:
        self.pattern = self.generate_named_pattern(
            pattern=self.pattern, keywords=self._converters.keys()
        )
        self._compiled_pattern = re.compile(
            pattern=self.pattern,
            flags=re.IGNORECASE,
        )

    @property
    def result(self) -> Dict[str, Any]:
        """
        Returns the result of the CommandValidator's converters as a dictionary of key-value pairs.

        :return: A dictionary containing the result of the CommandValidator.
        :rtype: Dict[str, Any]
        """
        return self._result

    @staticmethod
    def generate_named_pattern(pattern: str, keywords: List[str]) -> str:
        """
        Generates a named pattern by replacing the unnamed capture groups in the given pattern with named capture groups.

        Args:
            pattern (str): The pattern to generate the named pattern from.
            keywords (List[str]): The list of keywords to use for naming the capture groups.

        Returns:
            str: The generated named pattern.

        Example:
            >>> generate_named_pattern("(?:foo) (bar) (?:baz)", ["keyword1", "keyword2"])
            '(?P<keyword1>:foo) (?P<keyword2>(bar)) (?:baz)'

        Note:
            - The named capture groups are generated using the keywords provided.
            - The unnamed capture groups are replaced with named capture groups.
            - The named capture groups are enclosed in parentheses and prefixed with '?P<keyword>'.
            - The named capture groups are generated in the order of the keywords provided.
            - If no keywords are provided, the original pattern is returned.
        """
        if not keywords:
            return pattern
        keyword_iter = iter(keywords)
        try:
            segments = re.split(r"(\(.*?\))", pattern)
            processed = "".join(
                (
                    f"(?P<{next(keyword_iter)}>{segment[1:-1]})"
                    if not segment.startswith("(?:") and segment.startswith("(")
                    else segment
                )
                for segment in segments
                if segment
            )
        except StopIteration:
            pass
        return processed

    def accepts(self, data: str) -> bool:
        """
        Checks if the given data matches the compiled pattern and performs conversions on the matched groups.
        The converted values are stored in the result attribute.

        Args:
            data (str): The input data to check against the pattern.

        Returns:
            bool: True if the data matches the pattern and conversions are successful, False otherwise.
        """
        if not data:
            return False
        result: Optional[re.Match] = self._compiled_pattern.search(data)
        if result is None:
            return False

        self._result = {
            keyword: self._converters[keyword].convert(result.groupdict().get(keyword))
            for keyword in result.groupdict().keys()
        }
        self.result.update(
            {
                keyword: self._after_converters[keyword]["worker"].convert(
                    **{
                        k: self._result.get(k)
                        for k in worker["keywords"]
                        if k in result.groupdict()
                    }
                )
                for keyword, worker in self._after_converters.items()
            }
        )

        return True


@attrs.define
class LegacyAnswer:
    _string: str = attrs.field(default="", init=False, repr=False)
    _lines: list[str] = attrs.field(factory=list, init=False)
    unknown_answers: set[str] = attrs.field(factory=set)
    _valid: bool = attrs.field(default=False)
    _received: asyncio.Event = attrs.field(
        factory=asyncio.Event, init=False, repr=False
    )
    _received_timestamp: float | None = attrs.field(
        default=None, init=False, repr=False
    )
    _measured_response: float | None = attrs.field(default=None, init=False)
    _creation_timestamp: float = attrs.field(factory=time.time, init=False)

    @property
    def string(self) -> str:
        return self._string

    @property
    def lines(self) -> list[str]:
        return self._lines

    @property
    def valid(self) -> bool:
        return self._valid

    @valid.setter
    def valid(self, valid: bool) -> None:
        self._valid = valid

    @property
    def received(self) -> asyncio.Event:
        """
        Returns the asyncio.Event object representing the reception of the answer.

        :return: An asyncio.Event object.
        :rtype: asyncio.Event
        """
        return self._received

    @property
    def received_timestamp(self) -> float | None:
        """
        Returns the timestamp of when the answer was received.

        :return: A float representing the timestamp of when the answer was received, or None if the answer has not been received yet.
        :rtype: float | None
        """
        return self._received_timestamp

    @property
    def measured_response(self) -> float | None:
        """
        Returns the measured response value.

        :return: The measured response as a float, or None if the response is not measured yet.
        :rtype: float | None
        """
        return self._measured_response

    def reset(self) -> None:
        """
        Resets the state of the object to its initial state.

        This method clears the received flag, clears the lines list, sets the valid flag to False,
        sets the string attribute to an empty string, sets the creation timestamp to the current time,
        sets the measured response to None, and sets the received timestamp to None.

        Parameters:
            None

        Returns:
            None
        """
        self._received.clear()
        self._lines.clear()
        self._valid = False
        self._string = ""
        self._creation_timestamp = time.time()
        self._measured_response = None
        self._received_timestamp = None

    def receive_answer(self, answer: Iterable[str] | str) -> None:
        """
        Sets the received timestamp to the current time, processes the answer based on its type,
        calculates the measured response, and sets the received flag.

        Parameters:
            answer: Either an Iterable of strings or a single string as the received answer.

        Returns:
            None
        """
        self._received_timestamp = time.time()
        if isinstance(answer, Iterable) and not isinstance(answer, str):
            self._lines = list(answer)
            self._string = "\n".join(answer)
        elif isinstance(answer, str):
            self._lines = answer.splitlines()
            self._string = answer
        else:
            raise ValueError(f"{answer = } is not of type {str, list, tuple, set}")
        self._measured_response = self._received_timestamp - self._creation_timestamp
        self._received.set()


@attrs.define(hash=True, order=True, kw_only=True)
class LegacyCommand:
    argument: str = attrs.field(default="", converter=str)
    message: str = attrs.field(default="")
    estimated_response_time: float = attrs.field(default=5)
    expects_long_answer: bool = attrs.field(default=False, repr=False)
    _validators: List[LegacyAnswerValidator] = attrs.field(factory=list)
    answer: LegacyAnswer = attrs.field(init=False, factory=LegacyAnswer)
    _byte_message: bytes = attrs.field(init=False)
    _status_result: Dict[str, Any] = attrs.field(init=False, factory=dict)
    serial_communication: Optional[Communicator] = attrs.field(default=None)

    def __attrs_post_init__(self) -> None:
        if not isinstance(self._validators, (tuple, list, set, Generator)):
            self._validators = [self._validators]
        self._byte_message = f"{self.message}{self.argument}\n".encode(
            PLATFORM.encoding
        )

    @property
    def full_message(self) -> str:
        return f"{self.message}{self.argument}"  # MAYBE: add newline at the end

    @property
    def byte_message(self) -> bytes:
        return self._byte_message

    @property
    def validators(self) -> List[LegacyAnswerValidator]:
        return self._validators

    @validators.setter
    def validators(
        self, validators: Union[LegacyAnswerValidator, Iterable[LegacyAnswerValidator]]
    ) -> None:
        if isinstance(validators, LegacyAnswerValidator):
            self._validators = [LegacyAnswerValidator]
        elif isinstance(self, (list, tuple, set, Generator)):
            self._validators = list(validators)
        else:
            raise ValueError("Illegal value for validators", validators)

    @property
    def status_result(self) -> Dict[str, Any]:
        """
        Returns the status result of the object. This is a dictionary of key-value pairs containing
        all results of the CommandValidator's converters.

        :return: A dictionary containing the status result.
        :rtype: Dict[str, Any]
        """
        return self._status_result

    def add_validators(
        self, validators: Union[LegacyAnswerValidator, Iterable[LegacyAnswerValidator]]
    ) -> None:
        if isinstance(validators, LegacyAnswerValidator):
            self._validators.append(validators)
        elif isinstance(validators, (list, tuple, set, Generator)):
            self._validators.extend(validators)
        else:
            raise ValueError("Illegal argument for validators", validators)

    def set_argument(self, argument: Any) -> None:
        self.argument = argument
        self._byte_message = f"{self.message}{self.argument}\n".encode(
            PLATFORM.encoding
        )

    def get_dict(self) -> dict:
        return {"argument": self.argument, "message": self.message}

    async def execute(
        self, argument: Any = None, connection: Optional[Communicator] = None, should_log: bool = True
    ) -> tuple[LegacyAnswer, dict[str, Any]]:
        """
        Executes a command asynchronously.

        Args:
            argument (Any, optional): The argument for the command. Defaults to None.
            connection (Optional[Communicator], optional): The connection to use for executing the command. Defaults to None.

        Returns:
            tuple[Answer, dict[str, Any]]: A tuple containing the answer and the status result of the command.

        Raises:
            ValueError: If the serial communication reference is not viable.
            ConnectionError: If the device does not respond

        This method resets the answer, sets the argument if provided, and sends the command asynchronously using the specified connection.
        It then validates the answer and updates the status result with the received timestamp. Finally, it returns a tuple containing the answer and the status result.
        """
        if self.serial_communication is None and connection is None:
            raise ValueError(
                f"The serial communication reference is not viable. {self.serial_communication = } {type(self.serial_communication) = }"
            )

        if connection is None:
            assert self.serial_communication is not None
            connection = self.serial_communication

        self.answer.reset()
        if argument is not None:
            self.set_argument(argument)

        if should_log:
            parrot_feeder.debug("COMMAND_CALL(%s)", json.dumps(self.get_dict()))
        
        response = await connection.send_and_wait_for_response(self.full_message)

        self.answer.receive_answer(response.splitlines())
        self.answer.valid = self.validate()
        self.status_result.update({"timestamp": self.answer.received_timestamp})

        if should_log:
            parrot_feeder.debug("ANSWER(%s)", json.dumps({"message": self.answer.string}))

        return (self.answer, self.status_result)

    def validate(self) -> bool:
        """
        Validates the answer received from the command execution.

        This function checks if the answer has any lines. If not, it returns False.
        It then clears the unknown answers and status result.
        It updates the unknown answers with the lines of the answer.
        It iterates through each validator and checks if it accepts the entire string of the answer.
        If it does, it updates the status result and continues to the next validator.
        If not, it checks if any of the lines of the answer are accepted by the validator.
        If a line is accepted, it removes it from the unknown answers and updates the status result.
        If the entire string is accepted by at least one validator, it clears the unknown answers.
        Finally, it returns True if the number of lines in the answer is not equal to the number of unknown answers, otherwise False.

        Returns:
            bool: True if the answer is valid, False otherwise.
        """
        if not self.answer.lines:
            return False

        self.answer.unknown_answers.clear()
        self._status_result.clear()
        self.answer.unknown_answers = set(self.answer.lines)
        entire_string_accepted: bool = False
        accepted: bool = False

        for validator in self.validators:
            if validator.accepts(self.answer.string):
                entire_string_accepted = True
                accepted = True
                self._status_result.update(validator.result)
                continue
            for answer in self.answer.lines:
                if validator.accepts(data=answer):
                    accepted = True
                    self.answer.unknown_answers.discard(answer)
                    self._status_result.update(validator.result)

        if entire_string_accepted:
            self.answer.unknown_answers.clear()

        return accepted
