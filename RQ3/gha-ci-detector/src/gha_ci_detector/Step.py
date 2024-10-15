from typing import Optional, Callable


class Step:
    def __init__(self, yaml, is_inherited: bool = False):
        self.yaml: dict = yaml
        self.is_inherited = is_inherited

    def get_if(self) -> Optional[str]:
        if "if" in self.yaml.keys():
            return self.yaml["if"]
        else:
            return None

    def get_name(self) -> Optional[str]:
        if "name" in self.yaml.keys():
            return self.yaml["name"]
        else:
            return None

    def get_uses(self) -> Optional[str]:
        if "uses" in self.yaml.keys():
            return self.yaml["uses"]
        else:
            return None

    def get_execution(self) -> str:
        if (uses := self.get_uses()) is not None:
            return uses
        else:
            return self.yaml["run"]

    def get_line_numbers(self, get_line_number: Callable[[str, bool], int]) -> tuple[int, int]:
        numbers: list[int] = list(sorted(
            map(lambda k: get_line_number(f"{k}:{self.yaml[k]}".replace(" ", ""),
                                          False), self.yaml.keys())))
        return numbers[0], numbers[-1]

    def __eq__(self, other):
        if not isinstance(other, Step):
            return False
        if "uses" in self.yaml.keys() and "uses" in other.yaml.keys():
            return self.yaml["uses"] == other.yaml["uses"]
        elif "run" in self.yaml.keys() and "run" in other.yaml.keys():
            return self.yaml["run"] == other.yaml["run"]
        else:
            return False

