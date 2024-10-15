import json
import operator

import pandas as pd

if __name__ == '__main__':
    filenames = ["../output-python-final.xlsx"]
    project_count = 0
    commits = set()
    changes_count = 0
    label_project = {}
    label_count = {}
    label_language = {}
    all_projects = set()
    for filename in filenames:
        print(filename)
        xls = pd.ExcelFile(filename)
        # counter = 0
        for sheet in xls.sheet_names:
            labels_found = set()
            df = pd.read_excel(filename, sheet_name=sheet, index_col=[0])
            print(sheet)
            print(df)
            df = df.reset_index()
            if df.empty:
                continue
            project_count += 1
            for index, row in df.iterrows():
                all_projects.add(sheet)
                labels = row["Manual inspection"] if str(row["Manual inspection"]) != 'nan' else (
                    row)["Category"]
                labels = str(labels).strip()
                if 'nan' not in labels:
                    changes_count += 1
                    commits.add(row['URL'])
                # todo.add(filename + ' ' + sheet)
                labels = set(map(lambda x: str(x).strip(), labels.split("\n")))
                labels = set(filter(lambda x: x != 'nan' and x,
                                    labels))
                for label in labels:
                    if label not in label_count.keys():
                        label_count[label] = 0
                    label_count[label] = label_count[label] + 1
                    if label not in labels_found:
                        labels_found.add(label)

                    if label not in label_project:
                        label_project[label] = set()
                    if sheet not in label_project[label]:
                        label_project[label].add(sheet)
                    if label not in label_language:
                        label_language[label] = set()
                    if filename not in label_language[label]:
                        label_language[label].add(filename)
            print(df)
    print(label_count)
    # label_count = sorted(label_count.items(), key=operator.itemgetter(1))
    print(label_project)
    # print(todo)
    print(sum(label_count.values()))
    with open('output/labels.json', 'w') as f:
        f.write(json.dumps(label_count, indent=4))

    with open('output/projects.json', 'w') as f:
        for label in label_project.keys():
            label_project[label] = list(label_project[label])
        f.write(json.dumps(label_project, indent=4))

    with open('output/languages.json', 'w') as f:
        for label in label_language.keys():
            label_language[label] = list(label_language[label])
        f.write(json.dumps(label_language, indent=4))

    print(len(all_projects))

    print(f"Projects: {project_count}; Commits: {len(commits)}; Changes: {changes_count}")
