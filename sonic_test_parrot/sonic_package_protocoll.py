from dataclasses import dataclass
import re

@dataclass
class Package:
    destination: str
    source: str
    identifier: int
    content: str

    @property
    def length(self) -> int:
        return len(self.content)


class PackageParser:
    start_symbol = "<"
    end_symbol = ">"

    def parse_package(data: str) -> Package:
        regex = re.compile(r"<(.+)#(.+)#(\d+)#\d+#(.*)>", re.DOTALL)
        regex_match = re.search(regex, data)
        try:
            return Package(
                destination=regex_match.group(0),
                source=regex_match.group(1),
                identifier=int(regex_match.group(2)),
                content=regex_match.group(3)
            )
        except e:
            # TODO: error handling
            raise e


    def write_package(package: Package) -> str:
        return f"<{package.destination}#{package.source}#{package.identifier}#{package.length}#{package.content}>"
