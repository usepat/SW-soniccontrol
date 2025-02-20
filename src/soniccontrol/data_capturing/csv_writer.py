from pathlib import Path
from typing import List
import csv


class CsvWriter:
    def __init__(self):
        self._file = None

    def __del__(self):
        self.close_file()

    def _is_file_open(self) -> bool:
        return self._file and not self._file.closed

    def open_file(self, filename: Path, header: List[str]):
        self._file = open(filename, mode="w", newline="")
        self._writer = csv.writer(self._file)
        self._header = header

        self._writer.writerow(self._header)

    def write_entry(self, data: dict):
        if not self._is_file_open():
            return

        row: List[str] = []
        for col_name in self._header:
            if col_name not in data:
                raise IndexError(
                    f"the data provided is missing the field '{col_name}' of the header"
                )
            row.append(str(data[col_name]))

        self._writer.writerow(row)

    def close_file(self):
        if self._is_file_open():
            self._file.close()
