import json
import os
from os import listdir
from os.path import isfile, join
from typing import Optional, Annotated, Set

import typer

from gha_ci_detector import __app_name__, __version__, util
from gha_ci_detector.Workflow import Workflow
from gha_ci_detector.Runner import Runner

app = typer.Typer()


# def main():
#     app(prog_name=__app_name__)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()


@app.callback()
def main(version: Optional[bool] = typer.Option(
    None,
    "--version",
    "-v",
    help="Show application version and exit",
    callback=_version_callback, is_eager=True)) -> None:
    return


def analyze_and_report_workflow(workflow: Workflow, report: bool = True) -> Set[str]:
    runner = Runner(workflow)
    smells = runner.run_all()
    if report:
        util.print_smells(smells)
    if len(workflow.styling) > 0:
        print("The following styling errors were found: ")
        for s in workflow.styling:
            print(s)
    return smells


@app.command(name="all")
def analyze_all(workflow_folder: Annotated[Optional[str], typer.Argument()] = None) -> None:

    if workflow_folder is None:
        workflow_folder = "./.github/workflows"

    workflow_files = [join(workflow_folder, f) for f in listdir(workflow_folder)
                      if isfile(join(workflow_folder, f)) and (os.path.splitext(f)[1] == ".yml"
                                                               or os.path.splitext(f)[1] == ".yaml")]
    smell_count = {}
    all_smells = []
    for wf in workflow_files:
        workflow = Workflow.from_file(wf)
        all_smells += list(analyze_and_report_workflow(workflow))


@app.command(name="file")
def analyze_one(file_path: str = typer.Argument()) -> None:
    workflow = Workflow.from_file(file_path)
    analyze_and_report_workflow(workflow)
