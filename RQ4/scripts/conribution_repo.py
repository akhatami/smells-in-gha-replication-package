import codecs
import datetime
import json

from github import Github, Repository
from git import Repo

from github import Auth

from GitHub_Analyzer import check_for_workflow, setup_repo
from Project import Project

if __name__ == '__main__':
    file_name = "Repository-data/results-typescript-22-12-2023.json"
    file = codecs.open(file_name, encoding="utf-8", errors="ignore")
    projects_json = json.load(file)['items']
    sorted_projects = list(reversed(sorted(projects_json, key=lambda x: x['stargazers'])))[:100]
    projects = map(lambda x: {"id": x["id"], "name": x["name"]},
                   sorted_projects)
    auth = Auth.Token(token="")
    github = Github(auth=auth)
    finished_projects = []
    for p in projects:
        print(p["id"])
        print(p["name"])
        try:
            repo: Repository = github.get_repo(full_name_or_id=p["name"])
        except:
            continue
        merged_pr = repo.get_pulls(state="all", direction="dsc", sort="updated")

        merged_in_last_month = 0
        for pr in merged_pr:
            if pr.merged_at is None:
                continue
            print(pr)
            if datetime.date.today() - pr.merged_at.date() < datetime.timedelta(days=31):
                merged_in_last_month += 1
            else:
                break
        gh_project = Project(name=p["name"],
                             clone_url="https://github.com/{}.git".format(p["name"]), stars=0)
        repo: Repo = setup_repo(gh_project)
        check_for_workflow(repo, gh_project)
        if gh_project.has_workflow:
            p["merged_prs"] = merged_in_last_month
            finished_projects.append(p)
    print(list(finished_projects))
    sorted_projects = list(reversed(sorted(finished_projects, key=lambda x: x["merged_prs"])))
    for p in sorted_projects:
        print(f"{p['name']} has {p['merged_prs']} merged pr's in the last month")


