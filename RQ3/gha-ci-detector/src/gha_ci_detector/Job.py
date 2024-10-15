from typing import Optional

from gha_ci_detector.Step import Step


class Job:
    def __init__(self, name, yaml):
        self.name = name
        self.yaml: dict = yaml

    @property
    def job_name(self):
        if "name" in self.yaml.keys():
            return self.yaml["name"]
        else:
            return self.name

    def has_permissions(self):
        return "permissions" in self.yaml.keys()

    def get_steps(self) -> list[Step]:
        if "steps" in self.yaml.keys():
            return list(map(lambda x: Step(x), self.yaml["steps"]))
        else:
            return [Step({
                "uses": self.yaml["uses"]
            }, True)]

    def get_if(self) -> Optional[str]:
        if "if" in self.yaml.keys():
            return self.yaml["if"]
        else:
            return None

    def __str__(self):
        return "Job: \n" + self.name + " " + str(self.yaml) + "\n"

    def __repr__(self):
        return self.__str__()
