import os
import shutil
import subprocess
from tempfile import TemporaryDirectory

from mkite_core.models import JobInfo, JobResults, Status
from mkite_core.plugins import get_recipe
from mkite_engines import BaseConsumer, BaseProducer


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
        allow_restart: bool = False,
    ):
        self.src = src_engine
        self.dst = dst_engine
        self.err = error_engine
        self.archive = archive_engine
        self.compress = compress
        self.allow_restart = allow_restart

    def postprocess_all(self):
        done = []
        errors = []

        for key, folder in self.src.get_n(Status.DONE.value):
            try:
                jobid = self.postprocess_job(folder)
                done.append(key)

            except (PostprocessError, FileNotFoundError) as e:
                self.on_error(folder)
                errors.append(key)

        return done, errors

    def get_jobinfo(self, folder: os.PathLike):
        info_file = os.path.join(folder, JobInfo.file_name())

        if not os.path.exists(info_file):
            raise FileNotFoundError(f"JobInfo {JobInfo.file_name()} does not exist")

        try:
            info = JobInfo.from_json(info_file)
            return info

        except Exception as e:
            raise PostprocessError(f"Could not decode JobInfo. Error: {e}")

    def get_jobresults(self, folder: os.PathLike):
        results_file = os.path.join(folder, JobResults.file_name())

        if not os.path.exists(results_file):
            raise FileNotFoundError(f"Results {JobResults.file_name()} does not exist")

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
        compresslevel: int = 6,
    ) -> os.PathLike:
        if name is None:
            name = os.path.basename(folder)

        if not name.endswith(".tar.gz"):
            name += ".tar.gz"

        base_path = os.path.dirname(os.path.abspath(folder))

        with TemporaryDirectory(dir=base_path) as tmp:
            tar_path = os.path.join(tmp, name)
            compress_folder(folder, tar_path)

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
            new_info = recipe.handle_errors(delete_scratch=True)
        except Exception as e:
            raise PostprocessError(
                f"Failed to restart job for recipe {recipe_name}: {e}"
            )

        self.dst.push_info(recipe_name, new_info, status=Status.READY.value)

    def on_error(self, folder: os.PathLike):
        try:
            info = self.get_jobinfo(folder)

            if self.allow_restart:
                self.restart_job(info)
            else:
                self.dst.push_info(Status.ERROR.value, info, status=Status.ERROR.value)

        except FileNotFoundError as e:
            # cannot get the JobInfo from the folder
            print(e)

        except PostprocessError as e:
            print(e)
            # self.dst is the main engine (e.g., Redis)
            self.dst.push_info(Status.ERROR.value, info, status=Status.ERROR.value)

        finally:
            # self.err is where the error folders are stored locally
            self.err.push(Status.ERROR.value, folder)

        return


def compress_folder(src, dst):
    """Compresses the source folder src into the tar.gz file
    dst using the tar command"""
    src = os.path.abspath(src)
    base = os.path.dirname(src)
    name = os.path.basename(src)
    cmd = [
        "tar",
        "-czf",
        dst,
        "-C",
        base,
        name,
    ]
    return subprocess.run(cmd)


def compress_folder_python(src, dst):
    """Compresses the source folder src into the tar.gz file
    dst using the tarfile library. Can be extremely slow for
    larger tar files."""
    import tarfile

    with tarfile.open(dst, "w:gz", compresslevel=6) as tar:
        tar.add(src, arcname=os.path.basename(dst))
