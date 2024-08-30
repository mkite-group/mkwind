import os
from mkite_core.external import load_config
from pydantic import Field, DirectoryPath, FilePath
from pydantic_settings import BaseSettings


class EnvSettings(BaseSettings):
    """Wraps and obtains all settings for the environmental variables"""

    USER: str = Field(
        description="Username of the person running the jobs",
    )
    MAX_PENDING: int = Field(
        40,
        description="Maximum number of jobs pending on the queue",
    )
    MAX_RUNNING: int = Field(
        400,
        description="Maximum number of jobs running on the queue",
    )
    MAX_READY: int = Field(
        100,
        description="Maximum number of jobs in the READY folder",
    )
    SCHEDULER: str = Field(
        "slurm",
        description="Name of the scheduler to use",
    )
    ENGINE_LOCAL: FilePath = Field(
        ...,
        description="Config file for the local engine that will run the jobs",
    )
    ENGINE_EXTERNAL: FilePath = Field(
        ...,
        description="Config file for the external engine to use when pulling/pushing jobs",
    )
    ENGINE_ARCHIVE: FilePath = Field(
        ...,
        description="Config file for the external engine to use when archiving jobs",
    )
    LOG_PATH: DirectoryPath = Field(
        os.path.expanduser("~/logs"),
        description="Where the logs will be placed",
    )
    BUILD_CONFIG: FilePath = Field(
        None, 
        description="File containing the configuration files for building recipes",
    )

    class Config:
        case_sensitive = False

    @classmethod
    def from_file(cls, filename: FilePath):
        data = load_config(filename)
        return cls(**data)


def get_settings(path: os.PathLike = None) -> EnvSettings:
    if path is not None and os.path.exists(path):
        return EnvSettings.from_file(path)

    return EnvSettings()
