import datetime
import functools
import re
from enum import Enum

from pydriller import ModifiedFile

import util
from Change import Change
from GHA import Workflow
from util import list_concat


class Project:
    has_workflow = False

    def __init__(self, name: str, clone_url: str, stars: int):
        self.name = name
        self.clone_url = clone_url
        self.stars = stars
        self.modified_workflows: list[Modification] = []
        self.has_workflow = False

    def found_workflow(self):
        self.has_workflow = True

    def analyze_modifications(self) -> tuple[datetime, dict[int, int]]:
        self.modified_workflows.sort(key=lambda x: x.date)
        change_dictionary: dict[int, int] = {}
        if len(self.modified_workflows) == 0:
            return datetime.datetime.now(), change_dictionary
        start_date = self.modified_workflows[0].date
        for modification in self.modified_workflows:
            date_delta = (modification.date - start_date).days
            if date_delta not in change_dictionary:
                change_dictionary[date_delta] = 1
            else:
                change_dictionary[date_delta] = change_dictionary[date_delta] + 1
        print(change_dictionary)
        return start_date, change_dictionary

    def local_clone_url(self) -> str:
        if "https" not in self.clone_url:
            return self.clone_url
        return "../../repo_" + self.name

    def __str__(self) -> str:
        return "[Project] Name: {} \n Url: {} \n Has Workflow: {}".format(self.name,
                                                                          self.clone_url,
                                                                          self.has_workflow)

    def __repr__(self) -> str:
        return "[Project] Name: {} \n Url: {} \n Has Workflow: {}".format(self.name,
                                                                          self.clone_url,
                                                                          self.has_workflow)

    def is_local_project(self):
        return "https" not in self.clone_url


class Modification_Type(Enum):
    CHANGE = 'change'
    NEW = 'new'
    DELETE = 'delete'


class Modified_File:
    def __init__(self, file: str, diff: str, type: Modification_Type, change: ModifiedFile,
                 changes: list[Change] = None):
        self.name = file
        self.diff = diff
        self.type = type
        self.change: ModifiedFile = change
        regex = r"(?:@@ \-\d+,\d+ \+\d+,\d+ @@ .+\n)"
        _diffs = list(filter(lambda x: x != '', re.split(regex, change.diff)))
        self.changes: list[Change] = changes if changes is not None else list(
            map(lambda x: Change(x), _diffs))
        self.smells = set()

    def get_all_changes(self) -> list[str]:
        return functools.reduce(list_concat, self.changes, [])

    def get_all_additions(self) -> str:
        return functools.reduce(lambda acc, ch: acc + "\n".join(ch.get_new_snippet), self.changes, "")

    def get_all_removals(self) -> str:
        return functools.reduce(lambda acc, ch: acc + "\n".join(ch.get_old_snippet), self.changes, "")

    def get_yaml_before(self):
        return util.parse_yaml(self.change.source_code_before)

    def get_yaml_after(self):
        return util.parse_yaml(self.change.source_code)

    def get_workflow_before(self) -> Workflow:
        return Workflow(self.get_yaml_before())

    def __str__(self):
        return ("Modified file: " + self.name + " is " + str(self.type)
                + "\n Smells: " + " ".join(self.smells))

    def __repr__(self):
        self.__str__()


class Modification:
    def __init__(self, hash, date, commit_msg: str, files: list[Modified_File], is_merge: bool,
                 parent: str = None):
        self.commit_hash = hash
        self.date = date
        self.commit_msg = commit_msg
        self.files: list[Modified_File] = files
        self.is_merge = is_merge
        self.parent = parent

    def __repr__(self):
        return ("Modification on " + str(
            self.date) + " for hash " + self.commit_hash + " with message: "
                + self.commit_msg + "for files: \n" + str(self.files))

    def __str__(self):
        return self.__repr__()
