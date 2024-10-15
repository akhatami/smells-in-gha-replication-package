# RQ1

## Repository data
The data regarding the projects we used for RQ1 can be found in the folder `repository-data`. For each programming language there is a json file containing detailed information about the project (repository url, number of stars, etc.) which we used to select projects throughout the research.

## Labelling commits
The files output-*-.xlsx contain the commits we have analyzed for the selected projects in RQ1. Each commit is labelled with a one or multiple cateogories where the a new cateogory is always on a new line in the same cell.

## Script used
The scripts we used are located in [scripts](./scripts/). Before running any of the scripts don't forget to install the dependencies in [requirements.txt](./requirements.txt). 

- To find the 20 most popular projects used the [file_analyzer.py](./scripts/file_analyzer.py). 
- To analyze a whole project update the [project_analyzer.py](./scripts/project_analyzer.py) file to include the correct project and run this file. 
- We used the [label-counter.py](./scripts/label-counter.py) script to count all the labels in the excel files. 

## Detailed category count
[Common changes.xlsx](./Common%20changes.xlsx) contains a detail division of the changes we have found during our study. 

## Smells
The final list of smells can be found in [smell.xlsx](./smell.xlsx). 
This file contains the list of commits we found which fixes a smell. 
