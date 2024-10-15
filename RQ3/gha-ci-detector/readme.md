# GHA CI Detector
This tool provides CI analysis for GitHub Action workflows. 

## Getting started
Install hte latest version of our tool. 
This can be done by running `pip install dist/gha_ci_detector-0.0.3-py3-none-any.whl` in this directory. 

## Usage
### Running the tool
The tool can be run in two ways, either on a whole repository or on a specific file. 
In order to run on the `.github/workflows/` folder run `gha-ci-detector all` at the root level 
of your repository. If this is not possible, `gha-ci-detector all path/to/workflow/folder` can 
also be run where `path/to/workflow/folder` is the path pointing to the folder containing all 
the `.y(a)ml` files for the workflows. 

### Output
The tool will provide a console output with all the smells we were able to find for each workflow, including line numbers wherever possible. 

## Development
This tool is build using `poetry`. 
Use `poetry install` when changing something in the build files to make sure it still installs. 

In order to run the application in the command line, `gha_ci_detector` can be run as a python 
module using `python -m`. Make sure you're first in the `src` folder before doing this.
