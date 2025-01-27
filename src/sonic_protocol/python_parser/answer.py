

import logging
import re
import sys
from typing import Any, Callable, Dict, List,  Optional

import attrs

from sonic_protocol.field_names import EFieldName
from sonic_protocol.python_parser.converters import Converter
from sonic_protocol.defs import CommandCode, EFieldName


@attrs.define()    
class Answer:
    message: str = attrs.field(on_setattr=attrs.setters.NO_OP) 
    # TODO: probably better to make an enum ValidationStatus and merge valid and was_validated
    valid: bool = attrs.field(on_setattr=attrs.setters.NO_OP)
    was_validated: bool = attrs.field(on_setattr=attrs.setters.NO_OP)
    command_code: CommandCode | None = attrs.field(default=None)
    field_value_dict: Dict[EFieldName, Any] = attrs.field(default={})
    # received_timestamp: float = attrs.field(factory=time.time, init=False, on_setattr=attrs.setters.NO_OP)

    def is_error_msg(self) -> bool:
        return self.command_code is not None and self.command_code.value >= 20000

    @property
    def value_dict(self) -> Dict[EFieldName, Any]:
        return self.field_value_dict


@attrs.define()
class AfterConverter:
    convert_func: Callable = attrs.field()
    keywords: List[str] = attrs.field(default=[])


@attrs.define()
class AnswerValidator:
    pattern: str = attrs.field(on_setattr=attrs.setters.NO_OP)
    _named_pattern: str = attrs.field(init=False)
    _converters: Dict[EFieldName, Converter] = attrs.field(init=False, repr=False)
    _after_converters: Dict[EFieldName, AfterConverter] = attrs.field(init=False, repr=False)
    _compiled_pattern: re.Pattern[str] = attrs.field(init=False, repr=False)
    _field_names: Dict[str, EFieldName] = attrs.field(init=False, default={})


    def __init__(
        self,
        pattern: str,
        field_converters: Dict[EFieldName, Converter | AfterConverter] = {},
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
        workers: dict[EFieldName, Converter] = dict()
        after_workers: dict[EFieldName, AfterConverter] = dict()

        for keyword, worker in field_converters.items():
            if isinstance(worker, AfterConverter):
                after_workers[keyword] = worker
                continue

            workers[keyword] = worker
        
        self.pattern = pattern
        self._converters = workers
        self._after_converters = after_workers
        self._field_names = [field_name.value for field_name in self._converters.keys()]
            
        self._named_pattern = self.generate_named_pattern(
            pattern=self.pattern, keywords=self._field_names
        )
        self._compiled_pattern = re.compile(
            pattern=self._named_pattern,
            flags=re.IGNORECASE,
        )

    @staticmethod
    def generate_named_pattern(pattern: str, keywords: List[str]) -> str:
        """
        Generates a named pattern by replacing the unnamed capture groups in the given pattern with named capture groups.

        Args:
            pattern (str): The pattern to generate the named pattern from.
            keywords (List[str]): The list of keywords to use for naming the capture groups.

        Throws:
            throws an exception, if you do not pass the same number of keyword arguments as captured regex groups

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
        assert (next(keyword_iter, None) is None)

        return processed

    def validate(self, data: str) -> Answer:
        """
        Checks if the given data matches the compiled pattern and performs conversions on the matched groups.
        The converted values are stored in the result attribute.

        Args:
            data (str): The input data to check against the pattern.

        Returns:
            bool: True if the data matches the pattern and conversions are successful, False otherwise.
        """

        result: Optional[re.Match] = self._compiled_pattern.search(data)
        if result is None:
            return Answer(data, False, True)

        result_dict: Dict[EFieldName, Any] = {}
        for keyword, value in result.groupdict().items():
            field_name = EFieldName(keyword)
            converter = self._converters[field_name]

            if not converter.validate_str(value):
                return Answer(data, False, True) 
            result_dict[field_name] = converter.convert_str_to_val(value)

        for field_name, worker in self._after_converters.items():
            kwargs = {
                k: result_dict.get(field_name)
                for k in worker.keywords
                if k in result.groupdict()
            }
            result_dict[field_name] = worker.convert_func(kwargs)

        answer = Answer(data, True, True, field_value_dict=result_dict)

        return answer
