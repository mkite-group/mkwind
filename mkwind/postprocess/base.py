import os
import shutil
import tarfile
from tempfile import TemporaryDirectory

from mkite_core.models import JobInfo
from mkite_core.models import JobResults
from mkite_core.plugins import get_recipe
from mkite_engines import BaseConsumer
from mkite_engines import BaseProducer
from mkite_engines import Status


class PostprocessError(Exception):
    pass


class JobPostprocessor:
    def __init__(
        self,
        src_engine: BaseConsumer,
        dst_engine: BaseProducer,
        error_engine: BaseProducer,
        archive_engine: BaseProducer,
        compress: bool = True,
    ):
        self.src = src_engine
        self.dst = dst_engine
        self.err = error_engine
        self.archive = archive_engine
        self.compress = compress

    def postprocess_all(self):
        done = []
        errors = []

        for key, folder in self.src.get_n(Status.DONE.value):
            try:
                jobid = self.postprocess_job(folder)
                done.append(key)

            except PostprocessError as e:
                self.on_error(folder)
                errors.append(key)

        return done, errors

    def get_jobinfo(self, folder: os.PathLike):
        info_file = os.path.join(folder, JobInfo.file_name())

        if not os.path.exists(info_file):
            raise PostprocessError(f"JobInfo {JobInfo.file_name()} does not exist")

        try:
            info = JobInfo.from_json(info_file)
            return info

        except Exception as e:
            raise PostprocessError(f"Could not decode JobInfo. Error: {e}")

    def get_jobresults(self, folder: os.PathLike):
        results_file = os.path.join(folder, JobResults.file_name())

        if not os.path.exists(results_file):
            raise PostprocessError(f"Results {JobResults.file_name()} does not exist")

        try:
            info = JobResults.from_json(results_file)
            return info

        except Exception as e:
            raise PostprocessError(f"Could not decode JobResults. Error: {e}")

    def postprocess_job(self, folder: os.PathLike, delete: bool = True):
        info = self.get_jobresults(folder)
        jobid = self.get_jobid(info, folder)
        self.push_info_to_parsing(info)
        self.compress_folder(folder, name=jobid)

        if delete:
            shutil.rmtree(folder)

        return jobid

    def get_jobid(self, info: JobResults, folder: os.PathLike):
        if "uuid" in info.job:
            return info.job["uuid"]

        elif "id" in info.job:
            return str(info.job["id"])

        return os.path.basename(folder)

    def push_info_to_parsing(self, info: JobResults):
        return self.dst.push_info(
            Status.PARSING.value, info, status=Status.PARSING.value
        )

    def compress_folder(
        self,
        folder: os.PathLike,
        name: str = None,
    ) -> os.PathLike:
        if name is None:
            name = os.path.basename(folder)

        if not name.endswith(".tar.gz"):
            name += ".tar.gz"

        base_path = os.path.dirname(os.path.abspath(folder))

        with TemporaryDirectory(dir=base_path) as tmp:
            tar_path = os.path.join(tmp, name)
            with tarfile.open(tar_path, "w:gz") as tar:
                tar.add(folder, arcname=name)

            self.archive.push(Status.ARCHIVE.value, tar_path)

        return tar_path

    def restart_job(self, info: JobInfo) -> bool:
        recipe_name = info.recipe.get("name")
        if recipe_name is None:
            raise PostprocessError("JobInfo does not contain a recipe name")

        try:
            RecipeCls = get_recipe(recipe_name).load()
        except Exception as e:
            raise PostprocessError(f"Failed to load recipe: {e}")

        recipe = RecipeCls(info)
        try:
            new_info = recipe.handle_errors()
        except Exception as e:
            raise PostprocessError(
                f"Failed to handle errors for recipe {recipe_name}: {e}"
            )

        self.dst.push_info(recipe_name, new_info, status=Status.READY.value)

    def on_error(self, folder: os.PathLike):
        try:
            info = self.get_jobinfo(folder)
            self.restart_job(info)

        except PostprocessError as e:
            # self.dst is the main engine (e.g., Redis)
            self.dst.push_info(Status.ERROR.value, info, status=Status.ERROR.value)

        finally:
            # self.err is where the error folders are stored locally
            self.err.push(Status.ERROR.value, folder)

        return
