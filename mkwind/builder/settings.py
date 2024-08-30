import os
import json
from typing import List, Dict, Optional
from pathlib import Path
from collections.abc import Mapping
from mkite_core.external import load_config
from pydantic import Field, DirectoryPath, FilePath
from pydantic_settings import BaseSettings

from mkite_core.models import JobInfo


DEFAULT_CONFIG_NAME = "default.yaml"


def dict_update(d, u):
    for k, v in u.items():
        if isinstance(v, Mapping):
            d[k] = dict_update(d.get(k, {}), v)
        elif v is not None:
            d[k] = v
    return d


class JobSettings(BaseSettings):
    name: Optional[str] = Field(
        None,
        description="Name of the job to be executed",
    )
    account: Optional[str] = Field(
        None,
        description="Name of the account to charge HPC resources",
    )
    partition: Optional[str] = Field(
        None,
        description="Name of the partition where to run calculations",
    )
    nodes: int = Field(
        1,
        description="Number of nodes to use for a given job",
    )
    ntasks: Optional[int] = Field(
        None,
        description="Total number of tasks",
    )
    tasks_per_node: int = Field(
        8,
        description="Total number of tasks per node",
    )
    cpus_per_task: Optional[int] = Field(
        None,
        description="Total number of tasks",
    )
    gpus_per_task: Optional[int] = Field(
        None,
        description="Total number of GPUs per task",
    )
    gpus_per_node: Optional[int] = Field(
        None,
        description="Total number of GPUs per node",
    )
    gres: Optional[str] = Field(
        None,
        description="Resources to be used",
    )
    gpus: Optional[str] = Field(
        None,
        description="Total number of GPUs/resources",
    )
    walltime: str = Field(
        "30:00",
        description="Walltime for the job",
    )
    memory: Optional[str] = Field(
        None,
        description="Total memory allocated for the job",
    )
    memory_per_cpu: Optional[str] = Field(
        None,
        description="Total memory per CPU allocated for the job",
    )

    pre_cmd: Optional[str] = Field(
        None,
        description="Commands to execute prior to running the command",
    )
    cmd: Optional[str] = Field(
        None,
        description="Command to execute the package of interest",
    )
    post_cmd: Optional[str] = Field(
        None,
        description="Commands to execute after running the command",
    )

    @classmethod
    def from_yaml(cls, path: FilePath):
        data = load_config(path)
        return cls(**data)

    @classmethod
    def from_file_choices(cls, path: FilePath, choice: str, with_default: bool = True):
        original = load_config(path)
        data = {**original.get("default", {}), **original[choice]}

        return cls(**data)

    @staticmethod
    def get_choices(
        configs_path: os.PathLike, ftype="*.yaml", absolute_path: bool = False
    ):
        paths = Path(configs_path).rglob(ftype)

        if absolute_path:
            return [path.absolute() for path in paths]

        return [str(path.relative_to(configs_path)) for path in paths]

    def to_json(self, path: str):
        with open(path, "w") as f:
            json.dump(self.model_dump(), f)

    @staticmethod
    def file_name():
        return "runstats.json"


class AllJobSettings:
    """Aggregates the settings for building recipes based on the system.
    The settings should have the following format (example with YAML):

    ```
    default:
        account: account_name
        partition: partition_name
        ...
        post_cmd: touch mkwind-complete

    recipe:
        account: project_account
        ...
        pre_cmd: |
            module load package
        cmd: kite run
    ```
    The `recipe` key can be the recipe name itself
    (e.g., `vasp.pbe.relax`) or the name of the 
    package that will run the calculations
    (e.g. `vasp`). This allows several layers of 
    data sharing to be defined by the config, which
    helps when recipes are similar.

    The settings loaded by this function will return
    the settings loaded by `default`, `package`, then
    `recipe`.
    """

    def __init__(self, settings: Dict[str, dict]):
        self.settings = settings

    def __getitem__(self, key: str):
        return self.settings[key]

    @classmethod
    def from_file(cls, config_path: os.PathLike) -> "AllJobSettings":
        config = load_config(config_path)
        return cls(config)

    def get_recipe_settings(self, info: JobInfo) -> JobSettings:
        data = {}

        if "default" in self.settings:
            data = dict_update(data, self["default"])
        
        recipe = info.recipe["name"]
        package = recipe.split(".")[0]

        if package in self.settings:
            data = dict_update(data, self[package])

        if recipe in self.settings:
            data = dict_update(data, self[recipe])

        return JobSettings(**data)

    def config_has_recipe(self, recipe: str) -> bool:
        """checks if the settings for building recipes is available on the config_path.
        """

        package = recipe.split(".")[0]

        recipe_available = (package in self.settings or recipe in self.settings)

        return recipe_available
