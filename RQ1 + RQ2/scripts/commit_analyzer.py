import functools
import io
import re
import traceback

import editdistance
from git import Repo
from pydriller import Repository

import util
from Change import Change
from Project import Project, Modification_Type, Modified_File
from util import is_replace


def check_if_changes_equal(files: list[Modified_File]) -> list[Change]:
    _changes = functools.reduce(lambda acc, file: acc + file.changes, files, [])
    seen = set()
    duplicates = []
    for ch in _changes:
        if ch not in seen:
            seen.add(ch)
        else:
            duplicates.append(ch)
    return duplicates


def analyze_changes_in_commits(project: Project) -> None:
    for mod in project.modified_workflows:
        for file in mod.files:
            if file.type == Modification_Type.NEW:
                file.changes.append(Change(file.diff, ["Workflow added"]))
                continue
            elif file.type == Modification_Type.DELETE:
                file.changes.append(Change(file.diff, ["Workflow removed"]))
                continue
            regex = r"(?:@@ \-\d+,\d+ \+\d+,\d+ @@ .+\n)"

            _diffs = list(filter(lambda x: x != '', re.split(regex, file.diff)))
            file.changes = list(map(lambda x: Change(x), _diffs))
                # repository = Repository(project.local_clone_url())
                # print(mod.commit_hash)
                # print(mod.parent)
            try:
                check_file(file, mod.parent, project, mod.commit_hash)
            except Exception:
                print(project.name)
                print(traceback.format_exc())
            if len(file.changes) == 1:
                if is_a_small_removal(file.changes[0]):
                    file.changes[0].add_category("Only 1 line removed")
                if is_refactor_needs(file.changes[0]):
                    file.changes[0].add_category("Needs has been refactored")
                if change_workflow_name(file.changes[0]):
                    file.changes[0].add_category("Workflow is renamed")

            for _change in file.changes:
                if is_a_change_to_run_step(_change):
                    _change.add_category("Small change to run step")

                if adds_timeout(_change):
                    _change.add_category("Adds timeout")

                if (ch := is_env_change(_change)) != "":
                    _change.add_category("Env variable is {}".format(ch))

                if adds_a_permission(_change):
                    _change.add_category("Workflows must have permissions")

                if workflows_should_not_run_on_fork(_change):
                    _change.add_category("Workflows should not be run on forks")

                if add_matrix_scheme(_change):
                    _change.add_category("A matrix was added to the workflow")

                if uses_if_always(_change):
                    _change.add_category("Always run this job added")

                if adds_concurrency(_change):
                    _change.add_category("Adds concurrency")

                if is_indentation_fix(_change):
                    _change.add_category("Fix indentation")

        # If more than 1 file touched, check if any changes match
        # if len(mod.files) > 1:
        #     _changes = check_if_changes_equal(mod.files)
        #     for _change in _changes:
        #         print("Found a duplicate change!")
        #         _change.add_category("Duplicate change!")


def check_file(file, parent, project, commit):
    try:
        before_yaml = file.get_yaml_before()
    except Exception as e:
        print(e)
        before_yaml = util.get_yaml_failed(file, parent, project)

    try:
        after_yaml = file.get_yaml_after()
    except Exception as e:
        after_yaml = util.get_yaml_failed(file, commit, project)

    print(before_yaml)
    if "on" in before_yaml.keys():
        if "on" in after_yaml.keys():
            on_before = before_yaml["on"]
            on_after = after_yaml["on"]
            if "paths-ignore" not in on_before and "paths-ignore" in on_after:
                file.changes.append(Change(file.diff, ["Add paths-ignore"]))
            elif "paths" not in on_before and "paths" in on_after:
                file.changes.append(Change(file.diff, ["Add paths"]))
            elif on_after != on_before:
                file.changes.append(Change(file.diff, ["Update on"]))
        else:
            file.changes.append(Change(file.diff, ["Add on"]))

    jobs_before = before_yaml["jobs"]
    jobs_after = after_yaml["jobs"]

    if len(after_yaml) > len(before_yaml):
        file.changes.append(Change(file.diff, ["Job added"]))
        return
    elif len(after_yaml) < len(before_yaml):
        file.changes.append(Change(file.diff, ["Job removed"]))
        return
    elif before_yaml.keys() != after_yaml.keys():
        file.changes.append(Change(file.diff, ["Job renamed"]))
        return
    else:
        for k in jobs_before.keys():
            job_before = jobs_before[k]
            job_after = jobs_after[k]

            if len(job_before["steps"]) > len(job_after["steps"]):
                file.changes.append(Change(file.diff, ["Step removed"]))
            elif len(job_before["steps"]) < len(job_after["steps"]):
                file.changes.append(Change(file.diff, ["Step added"]))
            else:
                steps_before = job_before["steps"]
                steps_after = job_after["steps"]
                for i in range(len(steps_before)):
                    before = steps_before[i]
                    after = steps_after[i]



                    if "run" in before.keys():
                        if before["run"] != after["run"]:
                            file.changes.append(Change(file.diff, ["Update run command"]))
                        elif "with" in before.keys() and "with" in after.keys():
                            if before["with"] != after["with"]:
                                file.changes.append(Change(file.diff, ["Update action "
                                                                       "variable"]))
                    else:
                        if "with" in before.keys() and "with" in after.keys():
                            if before["with"] != after["with"]:
                                file.changes.append(Change(file.diff, ["Update action "
                                                                       "variable"]))
                        if before["uses"] != after["uses"]:
                            hashBefore = len(before["uses"].split("@")[1]) == 40
                            hashAfter = len(after["uses"].split("@")[1]) == 40
                            if after["uses"].split("@")[1] != before["uses"].split("@")[1]:
                                if hashBefore and not hashAfter:
                                    file.changes.append(Change(file.diff, ["Use hash instead "
                                                                           "of version "]))
                                elif hashBefore and hashAfter:
                                    file.changes.append(Change(file.diff, ["Bump hash "
                                                                           "version"]))
                                else:
                                    file.changes.append(Change(file.diff, ["Bump version"]))


                    if "env" in after.keys():
                        if "env" in before.keys():
                            if str(after["env"]) != str(before["env"]):
                                file.changes.append(Change(file.diff, ["Update env"]))
                        else:
                            file.changes.append(Change(file.diff, ["Update step"]))
            if "timeout-minutes" in job_after.keys():
                if "timeout-minutes" in jobs_before.keys():
                    if job_after["timeout-minutes"] != job_before["timeout-minutes"]:
                        file.changes.append(Change(file.diff, ["Update timeout"]))
                else:
                    file.changes.append(Change(file.diff, ["Add timeout"]))

    if "env" in after_yaml.keys():
        if "env" in before_yaml.keys():
            if str(before_yaml["env"]) != str(after_yaml["env"]):
                file.changes.append(Change(file.diff, ["Update env"]))
        else:
            file.changes.append(Change(file.diff, ["Update env"]))


def is_an_action_rename(_change: Change) -> bool:
    # They must equal otherwise we are doing more than renaming an action.
    if len(_change.added) == len(_change.removed) == 1:
        print(_change)
        # print(re.match(r"\s\s\s[a-zA-Z]([a-zA-Z0-9]+):", change.added[0]))
        is_action_name_added = re.match(r"\s\s\s[a-zA-Z]([a-zA-Z0-9_-]+):",
                                        _change.added[0]) is not None
        is_action_name_removed = (re.match(r"\s\s\s[a-zA-Z]([a-zA-Z0-9_-]+):",
                                           _change.removed[0]) is not None)
        # TODO check if the difference is behind the ':'
        return is_action_name_added and is_action_name_removed
    return False


def adds_timeout(_change: Change) -> bool:
    if "timeout: " in _change.added and ("timeout:" not in _change.removed):
        return True
    if "timeout-minutes: " in _change.added and ("timeout-minutes:" not in _change.removed):
        return True
    return False
    # if len(_change.added) == 1 and len(_change.removed) == 0:
    #     return "timeout-minutes: " in "\n".join(_change.added)
    # return False


def is_update_timeout(_change: Change) -> bool:
    if len(_change.added) == len(_change.removed) == 1:
        return ("timeout-minutes" in "\n".join(_change.added) and "timeout-minutes" in "\n".join(
            _change.removed))


def workflows_should_not_run_on_fork(_change: Change) -> bool:
    return ("if: github.repository ==" in "\n".join(_change.added)
            or "github.repository_owner ==" in "\n".join(_change.added)
            or "if: ${{ github.repository ==" in "\n".join(_change.added)
            or "contains(github.repository," in "\n".join(_change.added))


def is_a_step_rename(_change: Change) -> bool:
    """
    Check if a name attribute in the workflow file was changed.
    :param _change: The change to be evaluated.
    :return: True is only a name was changed, i.e. removed and added again.
    """
    if len(_change.added) == len(_change.removed) == 1:
        is_step_name_added = _change.added[0].startswith("    name:")
        is_step_name_removed = _change.removed[0].startswith("    name:")
        return is_step_name_added and is_step_name_removed
    return False


def is_a_small_removal(_change: Change) -> bool:
    """
    Check if only 1 line was removed. This usually means the commit is not interesting.
    :param _change: The change to be evaluated.
    :return: True if only 1 line was removed and none were added.
    """
    return len(_change.added) == 0 and len(_change.removed) == 1


def add_run_step_to_action(_change: Change) -> str:
    """
    Check if only a run step is added to the action.
    :param _change: The change to be evaluated.
    :return: True is only a run step is added.
    """
    # TODO: What if the run step also has a name?
    # Only new things get added.
    if len(_change.added) >= 1 and len(_change.removed) == 0:
        line = "\n".join(_change.added)
        # If we match the syntax of a run command.
        if re.match(r"\s\s\s\s-\s?run:.+", line) is not None:
            return "run step"
        if re.match(r"\s\s\s\s\s\s\s-\sname:\s(?:.+\n)+\s{9}run:\s(?:.+\n)", line):
            return "named run step"
        if re.match(r"\s\s\s\s\s\s\s-\suses:.+\n", line):
            return "action step"
    return ""


def change_workflow_name(_change: Change):
    if is_replace(_change):
        return ((re.match(r"\sname:\s(?:'|\")[a-zA-Z][a-zA-Z_-]+(?:'|\")",
                          _change.added[0]) is not None)
                and re.match(r"\sname:\s(?:'|\")[a-zA-Z][a-zA-Z_-]+(?:'|\")",
                             _change.removed[0]) is not None)
    return False


def add_matrix_scheme(_change: Change):
    if "matrix" in _change.added and (not "matrix" in _change.removed):
        return True
    return False


def is_a_change_to_run_step(_change: Change) -> bool:
    """
    Check if a run step is the only change.
    :param _change: The change to be evaluated.
    :return: Return true is the edit distance of the change is less than the length of the
    shortest line.
    """
    if len(_change.added) == len(_change.removed) == 1:
        if (re.match(r"[ \t]+-\srun:.+", _change.added[0])
                and re.match(r"[ \t]+-\srun:.+", _change.removed[0])):
            distance = editdistance.eval(_change.added[0], _change.removed[0])
            print(distance)
            return distance <= min(len(_change.added[0]), len(_change.removed[0]))
    return False


def change_cron_timing(_change: Change) -> bool:
    if len(_change.added) == len(_change.removed) == 1:
        if (_change.added[0].startswith("     - cron:")
                and _change.removed[0].startswith("     - cron:")):
            return True
    return False


def is_adding_an_action(_change: Change) -> bool:
    if len(_change.removed) == 0:
        full_text = "\n".join(_change.added)
        return re.match(r"\s\s\s[a-zA-Z][a-zA-Z0-9_-]+:\n(?:.+\n)+\s\s\s\s\ssteps:\n("
                        r"?:\s\s\s\s\s\s.+\n?)+", full_text) is not None
    return False


def is_refactor_needs(_change: Change) -> bool:
    if len(_change.removed) == len(_change.added) == 1:
        return re.match(r"[ \t]+\sneeds: \[.+\]", _change.added[0]) is not None and re.match(
            r"[ \t]+\sneeds: \[.+\]", _change.removed[0]) is not None


def is_env_change(_change: Change) -> str:
    if re.match(r"\s{5}env:\n(\s{7}.+:.+\n)+\+\s{6}.+:", _change.get_new_snippet()):
        if re.match(r"\s{5}env:\n(\s{7}.+:.+\n)+\-\s{6}.+:", _change.get_old_snippet()):
            return "updated"
        else:
            return "added"
    return ""


def uses_if_always(_change: Change) -> bool:
    if "always()" in _change.added and ("always()" not in _change.removed):
        return True
    elif "failure()" in _change.added and("failure()" not in _change.removed):
        return True
    elif "cancelled()" in _change.added and ("cancelled()" not in _change.removed):
        return True
    return False


def adds_a_permission(_change: Change) -> bool:
    return (("permissions: " not in "\n".join(_change.removed))
            and ("permissions:" in "\n".join(_change.added)))

def updates_on(_file):
    for _change in _file.changes:
        paths_before = set()
        paths_after = set()
        before = _file.get_yaml_before()
        after = _file.get_yaml_after()
        if "on" in before.keys():
            on_before = before["on"]
            if isinstance(on_before, dict):
                for key in on_before.keys():
                    if on_before[key] is not None and isinstance(on_before[key], dict):
                        if "paths-ignore" in on_before[key].keys():
                            for el in list(on_before[key]["paths-ignore"]):
                                paths_before.add(el)
                        if "paths" in on_before[key].keys():
                            for el in list(on_before[key]["paths"]):
                                paths_before.add(el)
        if "on" in after.keys():
            on_after = after["on"]
            if isinstance(on_after, dict):
                for key in on_after.keys():
                    if on_after[key] is not None and isinstance(on_after[key], dict):
                        if on_after[key] is not None and "paths-ignore" in on_after[key].keys():
                            for el in list(on_after[key]["paths-ignore"]):
                                paths_after.add(el)
                        if on_after[key] is not None and "paths" in on_after[key].keys():
                            for el in list(on_after[key]["paths"]):
                                paths_after.add(el)
        current_change = False
        for path in paths_after:
            if path in _change.get_new_snippet():
                current_change = True
        if len(paths_after) > len(paths_before) and current_change:
            _file.smells.add("Avoid running CI related actions when no source code has changed")
    # TODO: Also check if there is an 'if' statement for something?

def pull_based_actions_on_fork(_file: Modified_File) -> None:
    """
    Check if the 'if' statement is added somewhere, also make sure that the action we are doing
    is 'the correct one'
    :param _file:
    :return:
    """
    for _change in _file.changes:
        if ("if: github.repository ==" in "\n".join(_change.added)
                or "github.repository_owner ==" in "\n".join(_change.added)
                or "if: ${{ github.repository ==" in "\n".join(_change.added)
                or "if: ${{ github.repository_owner ==" in "\n".join(_change.added)
                or "contains(github.repository," in "\n".join(_change.added)):

            # TODO: Maybe we can extend this further?
            is_pull_based_action = ("pr" in _file.name or "issue" in _file.name or "review" in
                                    _file.name)
            # print(_file.name)
            if is_pull_based_action:
                _file.smells.add("Prevent pull-based development actions on forks")

def adds_concurrency(_change: Change) -> bool:
    return (("concurrency:" in "\n".join(_change.added)
             and ("concurrency:" not in "\n".join(_change.removed))))


def is_indentation_fix(_change: Change) -> bool:
    stripped_removed = list(map(lambda x: x.strip(), _change.removed))
    stripped_added = list(map(lambda x: x.strip(), _change.added))
    return stripped_added == stripped_removed


if __name__ == "__main__":
    diff = """@@ -242,6 +242,23 @@ jobs:
     env:
       NEXT_TELEMETRY_DISABLED: 1
+      HEADLESS: true
-      HEADLESS: false
       NEXT_PRIVATE_SKIP_SIZE_TESTS: true
     strategy:
       fail-fast: false
       matrix:


"""
    diffs = list(filter(lambda x: x != '', re.split(r"(?:@@ \-\d+,\d+ \+\d+,\d+ @@ .+\n)", diff)))
    # Remove all the lines which are not related to the diff
    changes: list[Change] = list(map(lambda x: Change(x), diffs))
    for change in changes:
        print(change)
        print(is_env_change(change))
