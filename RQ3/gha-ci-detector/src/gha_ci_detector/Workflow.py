from typing import Optional

import gha_ci_detector.util as util
from gha_ci_detector.Job import Job


class Workflow:
    def __init__(self, file_content: str, name: str = ""):
        self.file_content: str = file_content
        self.yaml: dict = util.parse_yaml(file_content)
        self.name = name
        self.smells = set()
        self.styling = []

    @classmethod
    def from_file(cls, filepath):
        data = open(filepath).read()
        return cls(data, filepath)

    def get_jobs(self) -> list[Job]:
        jobs = self.yaml['jobs']
        return list(map(lambda x: Job(x, self.yaml['jobs'][x]), jobs))

    def get_keys(self) -> list[str]:
        return list(self.yaml.keys())

    def get_on(self) -> Optional[dict]:
        if 'on' in self.yaml.keys():
            return self.yaml["on"]
        else:
            return None

    def __get_stripped_lines(self) -> list[str]:
        return list(map(lambda x: x.replace("-", "").strip(), self.file_content.split("\n")))

    def __get_lines_without_spaces(self) -> list[str]:
        return list(map(lambda x: x.replace("-", "").replace(" ", ""), self.__get_stripped_lines()))

    def get_line_number(self, line: str, use_whitespace: bool = True) -> Optional[int]:
        try:
            if use_whitespace:
                return self.__get_stripped_lines().index(line.replace("-", "")) + 1
            else:
                return self.__get_lines_without_spaces().index(line.replace("-", "")) + 1
        except ValueError:
            return -1

