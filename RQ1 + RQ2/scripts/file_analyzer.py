import codecs
import json

import requests

import Scraper
from Project import Project


def clone_url_api(project_name: str) -> str:
    url = ("https://api.github.com/search/repositories?q={}+in%3Aname").format(project_name)
    request = requests.get(url, headers=Scraper.headers)
    if request.status_code == 200:
        projects = request.json()['items']
        return projects[0]['clone_url']


def clone_url(project_name: str) -> str:
    return "https://github.com/{}.git".format(project_name)


def get_projects_from_file(file: str) -> list[Project]:
    with codecs.open(file, encoding="utf-8", errors="ignore") as file:
        projects_json = json.load(file)['items']
        sorted_projects = list(reversed(sorted(projects_json, key=lambda x: x['stargazers'])))[:20]
        projects = map(lambda x: Project(x['name'], clone_url(x['name']), x['stargazers']),
                       sorted_projects)
        return list(projects)


if __name__ == "__main__":
    print(get_projects_from_file('Repository-data/results-javascript-22-12-2023.json'))
