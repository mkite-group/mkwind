import os
import shutil
from typing import Union
from tempfile import TemporaryDirectory

from mkite_core.models import JobInfo, Status
from mkite_engines import BaseConsumer, LocalProducer
from mkwind.user import EnvSettings
from mkwind.templates import Template

from .settings import JobSettings, AllJobSettings


class BuilderError(Exception):
    pass


class JobBuilder:
    def __init__(
        self,
        src_engine: BaseConsumer,
        dst_engine: LocalProducer,
        settings: EnvSettings,
        template: Template,
        explicit_config: bool = True,
        delete_on_build: bool = False,
    ):
        self.src = src_engine
        self.dst = dst_engine
        self.template = template
        self.explicit_config = explicit_config
        self.recipe_settings = AllJobSettings.from_file(settings.BUILD_CONFIG)
        self.delete_on_build = delete_on_build

    def get_ready(self):
        ready_jobs = self.dst.list_queue(Status.READY.value)
        return len(ready_jobs)

    def get_src_queues(self, allowed_only=True):
        queues = self.src.list_queue_names()

        if not allowed_only:
            return queues

        return [q for q in queues if self.building_is_allowed(q)]

    def building_is_allowed(self, recipe: str) -> bool:
        if self.explicit_config:
            return self.recipe_settings.config_has_recipe(recipe)

        # allows building as long as it is not a queue name
        return not Status.has_value(recipe)

    def build_all(self, max_build: int = 1000):
        n = 0
        built = []

        for queue in self.get_src_queues():
            while n < max_build:
                key, info = self.src.get_info(queue)
                if info is None:
                    break

                job_folder = self.build_job(info)
                built.append(job_folder)

                if self.delete_on_build:
                    self.src.delete(key)
                n += 1

        return built

    def build_job(self, info: JobInfo) -> os.PathLike:
        job_settings = self.get_settings(info)

        with TemporaryDirectory() as tmp:
            job_folder = self.make_folder(info, root=tmp)
            self.write_template(job_folder, job_settings)
            self.write_info(info, job_folder, JobInfo.file_name())
            self.write_info(job_settings, job_folder, JobSettings.file_name())

            dst = self.dst.push(Status.READY.value, job_folder)

        return dst

    def make_folder(self, info: JobInfo, root: os.PathLike) -> os.PathLike:
        path = os.path.join(root, info.folder_name)
        if os.path.exists(path):
            raise BuilderError("Trying to build jobs with the same name.")

        os.mkdir(path)
        return path

    def get_settings(self, info: JobInfo) -> JobSettings:
        return self.recipe_settings.get_recipe_settings(info)

    def get_recipe_name(self, info: JobInfo) -> str:
        return info.recipe.get("name", Status.ANY.value)

    def write_info(
        self, info: Union[JobInfo, JobSettings], folder: os.PathLike, name: str
    ):
        return info.to_json(os.path.join(folder, name))

    def write_template(
        self, job_folder: os.PathLike, settings: JobSettings
    ) -> os.PathLike:
        return self.template.render_to(settings.model_dump(), job_folder)
