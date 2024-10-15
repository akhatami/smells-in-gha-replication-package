import glob
import os.path
import re
import threading
import time

import matplotlib.pyplot as plt
import xlsxwriter

from git import Repo
from pydriller import Repository, ModifiedFile

import file_analyzer
import util
from GHA import Workflow
from Project import Project, Modification_Type, Modified_File, Modification
import shutil

from commit_analyzer import analyze_changes_in_commits
from util import fill_dict


def setup_repo(project: Project) -> Repo:
    if "https" not in project.clone_url:
        return Repo(project.clone_url)

    if os.path.isdir(project.local_clone_url()):
        shutil.rmtree(project.local_clone_url())
    #
    # return Repo(local_url)
    finished = False
    repo = None
    while not finished:
        try:
            print(project.clone_url)
            repo = Repo.clone_from(project.clone_url, project.local_clone_url())
            finished = True
            print("Cloned " + project.name)
        except Exception as e:
            print("Unable to clone" + project.name + ", trying again in 5 min...")
            print(e)
            time.sleep(1 * 60)
    return repo


def check_for_workflow(repo: Repo, project: Project):
    try:
        if os.path.isdir(project.local_clone_url() + '/.github/workflows'):
            # Should check if it contains yaml files
            print("workflow folder found!")
            project.found_workflow()
        else:
            print("No workflow found!")
    except Exception as e:
        print("Exception thrown")
        print(e)


def parse_file_change(file : ModifiedFile):
    # If there is no .y(a)ml extension this is definetly not a workflow.
    if ".yaml" not in file.filename and ".yml" not in file.filename:
        return None

    # If we do have a .y(a)ml file, then check if it is in the workflows folder
    # and gather some information about the change if it is.
    # type: Modification_Type = Modification_Type.CHANGE
    path = ""
    file_name = ""
    if file.old_path is None:
        path = file.new_path
        file_regex = re.search("github\/workflows\/(.*\.y(a?)ml)", path)
        if file_regex is None:
            return None
        file_name = file_regex.group(1)
        type = Modification_Type.NEW
    elif file.new_path is None:
        path = file.old_path
        file_regex = re.search("github\/workflows\/(.*\.y(a?)ml)", path)
        if file_regex is None:
            return None
        file_name = file_regex.group(1)
        type = Modification_Type.DELETE
    else:
        type = Modification_Type.CHANGE
        path = file.new_path
        file_regex = re.search("github\/workflows\/(.*\.y(a?)ml)", path)
        if file_regex is None:
            return
        file_name = file_regex.group(1)
    # print(file.diff)
    # print("\n")
    return Modified_File(file_name, file.diff, type, file)


def find_changes_in_workflow(project: Project):
    repository = Repository(project.local_clone_url())
    first_commit = ''
    # We do not care about merge commits.
    # traverse_commits = filter(lambda x: not x.merge, repository.traverse_commits())
    traverse_commits = repository.traverse_commits()
    for commit in traverse_commits:
        if first_commit == '':
            first_commit = commit.hash
        modified_workflows: list[Modified_File] = list(
            filter(lambda x: x is not None, map(parse_file_change,
                                                commit.modified_files)))
        if len(modified_workflows) != 0:
            parent = commit.parents[0] if len(commit.parents) > 0 else first_commit
            (project.modified_workflows
             .append(Modification(commit.hash, commit.author_date, commit.msg,
                                  modified_workflows, commit.merge, parent)))

    if not project.is_local_project():
        shutil.rmtree(project.local_clone_url())


def write_changes_to_file(projects: list[Project], file: str):
    workbook = xlsxwriter.Workbook(file)
    total_changes = 0
    catagorized_changes = 0
    for project in projects:
        try:
            worksheet = workbook.add_worksheet(('project - ' + project.name.replace("/",
                                                                                    " "))[0:30])
        except Exception:
            name = str(hash(project.name))
            worksheet = workbook.add_worksheet(('project - ' + name[0:30]))

        bold = workbook.add_format({"bold": True})
        merge_format = workbook.add_format({
            "text_wrap": "true"
        })
        worksheet.write("A1", "URL", bold)
        worksheet.write("B1", "Commit Text", bold)
        worksheet.write("C1", "Merge", bold)
        worksheet.write("D1", "File Name", bold)
        worksheet.write("E1", "Inspection", bold)
        worksheet.write("F1", "Auto inspection", bold)
        worksheet.write("G1", "Category", bold)
        worksheet.write("H1", "Manual inspection", bold)
        current_row = 2
        for modification in project.modified_workflows:
            entry_start_row = current_row
            url = project.clone_url.replace(".git", "") + "/commit/" + modification.commit_hash
            files = modification.files
            for i, file in enumerate(files):
                total_changes = total_changes + 1
                worksheet.write('D' + str(current_row), file.name)
                if file.get_all_changes() is not None and len(file.get_all_changes()) > 0:
                    catagorized_changes = catagorized_changes + 1
                    worksheet.write_formula('E' + str(current_row),
                                            "=IF(ISBLANK(F" + str(current_row) + "),H" + str(
                                                current_row) + ",F" + str(current_row) + ")")

                    worksheet.write('F' + str(current_row), '\n'.join(file.get_all_changes()))
                    worksheet.write('G' + str(current_row), '\n'.join(file.get_all_changes()))
                current_row += 1
            if not current_row - 1 == entry_start_row:
                worksheet.merge_range("A" + str(entry_start_row) + ":A" + str(current_row - 1),
                                      url,
                                      merge_format)
                worksheet.merge_range("B" + str(entry_start_row) + ":B" + str(current_row - 1),
                                      modification.commit_msg, merge_format)
                worksheet.merge_range("C" + str(entry_start_row) + ":C" + str(current_row - 1),
                                      modification.is_merge, merge_format)
            else:
                worksheet.write("A" + str(entry_start_row), url, merge_format)
                worksheet.write("B" + str(entry_start_row), modification.commit_msg,
                                merge_format)
                worksheet.write("C" + str(entry_start_row), modification.is_merge,
                                merge_format)

        worksheet.autofit()
    workbook.close()
    print("{}/{} changes are catagorized!".format(catagorized_changes, total_changes))


def work_on_project(gh_project: Project):
    repo: Repo = setup_repo(gh_project)
    check_for_workflow(repo, gh_project)
    find_changes_in_workflow(gh_project)

    analyze_changes_in_commits(gh_project)

    # number_of_steps_per_action(gh_project)

    (start_time, changes) = gh_project.analyze_modifications()
    (counts, time_stamps) = fill_dict(changes)
    plt.title("Changes over time - " + gh_project.name)
    plt.plot(time_stamps, counts, "--")
    plt.show()
    # plt.savefig('img/' + gh_project.name.replace("/", " ") + ".png")


def find_action_with_timeout(gh_project: Project, return_list: list, i: int):
    repo: Repo = setup_repo(gh_project)
    check_for_workflow(repo, gh_project)
    timeout_steps = {}
    if not gh_project.found_workflow():
        return

    for f in glob.glob(gh_project.local_clone_url() + '/.github/workflows/*.yaml'):
        file = open(f, 'r')
        content = file.read()
        if 'timeout-minutes' in content:
            workflow = Workflow(util.parse_yaml(content))
            for job in workflow.get_jobs():
                for step in job.get_steps():
                    if "timeout-minutes" in step.yaml.keys():
                        timeout = step.yaml["timeout-minutes"]
                        if "run" in step.yaml.keys():
                            step = step.yaml["run"]
                        else:
                            step = step.yaml["uses"]
                        timeout_steps[step] = timeout
    return_list[i] = timeout_steps


if __name__ == "__main__":
    projects = file_analyzer.get_projects_from_file(
        'Repository-data/results-javascript-22-12-2023.json')
    threads = []
    # return_dicts: list[dict] = []
    for index, gh_project in enumerate(projects):
        t = threading.Thread(target=work_on_project, args=(gh_project,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    for project in projects:
        total_changes = 0
        categorized_changes = 0
        for mod in project.modified_workflows:
            for file in mod.files:
                total_changes += 1
                if file.get_all_changes() is not None and len(file.get_all_changes()) > 0:
                    categorized_changes += 1
        print(f"{project.name} has {categorized_changes}/{total_changes}")

    # final_dict = {}
    # for dict in return_dicts:
    #     for key in dict.keys():
    #         if key in final_dict:
    #             final_dict[key].append(int(dict[key]))
    #         else:
    #             final_dict[key] = [int(dict[key])]
    #
    # print(final_dict)
    # for key in final_dict.keys():
    #     print(key)
    #     print(sum(final_dict[key]) / len(final_dict[key]))

    # write_changes_to_file(projects,  'output-typescript-final.xlsx')



    # project = Project("nextjs", "../nextjs", 0)
    # work_on_project(project)
    # number_of_steps_per_action(project)
    # write_changes_to_file([project], 'output-nextjs.xlsx')
