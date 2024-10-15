import copy
import io
import os
import shutil
import time
from typing import Callable

from git import Repo
from pydriller import Repository

from Change import Change

from ruamel.yaml import YAML

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


list_concat: Callable[[list[str], Change], list[str]] = lambda acc, ch: (acc + ch.categories)


def is_replace(_change: Change) -> bool:
    return len(_change.added) == len(_change.removed) == 1


def parse_yaml(yaml_str: str | None) -> dict | None:
    if yaml_str is None:
        return None
    yaml = YAML()
    try:
        content = yaml.load(io.StringIO(yaml_str))
        return content
    except Exception:
        print("Unable to parse yaml file: " + yaml_str)
        return None

def setup(project):
    if "https" not in project.clone_url:
        return Repo(project.clone_url + "_copy")

    if os.path.isdir(project.local_clone_url() + "_copy"):
        # shutil.rmtree(project.local_clone_url())
        return Repo(project.local_clone_url() + "_copy")
    #
    # return Repo(local_url)
    finished = False
    repo = None
    while not finished:
        try:
            print(project.clone_url)
            repo = Repo.clone_from(project.clone_url, project.local_clone_url() + "_copy")
            finished = True
            print("Cloned " + project.name)
        except Exception as e:
            print("Unable to clone" + project.name + ", trying again in 5 min...")
            print(e)
            time.sleep(1 * 60)
    return repo


def get_yaml_failed(file, parent: str, project) -> dict:
    print("parent" + parent)
    repo = setup(project)
    repo.git.checkout(parent)
    f = open(project.local_clone_url() + "_copy/.github/workflows/" + file.name)
    before = f.read()
    before_yaml = parse_yaml(before)
    # print(before_yaml)
    return before_yaml
