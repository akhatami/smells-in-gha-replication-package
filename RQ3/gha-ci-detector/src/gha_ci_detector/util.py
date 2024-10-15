import io

from ruamel.yaml import YAML
from typing import Optional, Callable



def parse_yaml(yaml_str: Optional[str]) -> Optional[dict]:
    if yaml_str is None:
        return None
    yaml = YAML()
    try:
        content = yaml.load(io.StringIO(yaml_str))
        return content
    except Exception as e:
        print("Unable to parse yaml file: " + yaml_str)
        print(e)
        return None


def print_smells(smells: set) -> None:
    print(f"We have found {len(smells)} smells")
    ordered_smells = list(smells)
    ordered_smells.sort(key=lambda x: int(x.split(".")[0]))
    for s in ordered_smells:
        print("\t- " + s)



def fill_dict(mods: dict[int, int]) -> (list[int], list[int]):
    if len(mods.keys()) == 0:
        return [], []
    time_stamps = [i for i in range(1, list(mods.keys())[-1])]
    counts = []
    last = 0
    for el in time_stamps:
        try:
            last = mods[el] + last
            counts.append(last)
        except KeyError:
            counts.append(last)
    return counts, time_stamps

