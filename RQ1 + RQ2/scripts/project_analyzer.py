import io
import threading
import traceback
from typing import Any

import pandas as pd
from git import Repo
from ruamel.yaml import YAML

from Change import Change
from GitHub_Analyzer import setup_repo, find_changes_in_workflow, write_changes_to_file
from Project import Project, Modification_Type
from commit_analyzer import analyze_changes_in_commits


def parse_yaml(yaml_str: str) -> dict | None:
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

def do_work(project):
    project.found_workflow()
    repo: Repo = setup_repo(project)
    find_changes_in_workflow(project)
    analyze_changes_in_commits(project)
    write_changes_to_file([project], project.name + ".xlsx")


if __name__ == '__main__':
    # Python
    projects = [
        # Project("pytorch", "https://github.com/pytorch/pytorch.git" ,0)
        # Project("material-ui", "https://github.com/mui/material-ui.git", 0),
        # Project("Vite", "https://github.com/vitejs/vite.git", 0),
        # Project("echarts", "https://github.com/apache/echarts.git", 0),
    ]
    # project = Project("typescript", "https://github.com/microsoft/typescript.git", 0)

    # Typescript
    projects = [
        Project("realworld", "https://github.com/gothinkster/realworld.git", 0),

    ]
    # do_work(projects[0])
    threads = []
    for project in projects:
        t = threading.Thread(target=do_work, args=(project,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
