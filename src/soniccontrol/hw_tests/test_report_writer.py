from pathlib import Path
from typing import List
from soniccontrol.hw_tests.test_base import TestInfo, TestResult
import importlib.resources as rs
import jinja2
import soniccontrol


class TestReportWriter:
    @staticmethod
    def write_test_report(tests: List[TestInfo], file_path: Path):
        template_path = rs.files(soniccontrol).joinpath("hw_tests/jinja")
        environment = jinja2.Environment(loader=jinja2.FileSystemLoader(str(template_path)))

        template = environment.get_template("test_report.j2")
        content = template.render(
            tests=tests
        )

        with open(file_path, "w") as f:
            f.write(content)


def main():
    tests = [
        TestInfo(0, "test 1", "suite 1", TestResult(True, "yeaaahhh")),
        TestInfo(1, "test 2", "suite 1", None),
        TestInfo(2, "test 3", "suite 1", TestResult(False, "nooooo")),
    ]
    Path("./output").mkdir(exist_ok=True, parents=True)
    TestReportWriter.write_test_report(tests, Path("./output/test_report.html"))


if __name__ == "__main__":
    main()
