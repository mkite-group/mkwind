import os
import shutil
import tarfile
from tempfile import TemporaryDirectory

from mkite_core.models import JobResults
from mkite_engines import BaseProducer, BaseConsumer, Status


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

        for folder in self.src.get_n(Status.DONE.value):
            fname = os.path.basename(folder)
            try:
                jobid = self.postprocess_job(folder)
                done.append(jobid)

            except PostprocessError as e:
                self.on_error(folder)
                errors.append(fname)

        return done, errors

    def get_info(self, folder: os.PathLike):
        results_file = os.path.join(folder, JobResults.file_name())

        if not os.path.exists(results_file):
            raise PostprocessError(f"Results {JobResults.file_name()} does not exist")

        try:
            info = JobResults.from_json(results_file)
            return info

        except Exception as e:
            raise PostprocessError("Could not decode JobResults. Error: {e}")

    def postprocess_job(self, folder: os.PathLike, delete: bool = True):
        info = self.get_info(folder)
        jobid = self.get_jobid(info, folder)
        out = self.push_info_to_parsing(info)
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
        return self.dst.push_info(Status.PARSING.value, info, status=Status.PARSING.value)

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

    def on_error(self, folder: os.PathLike):
        return self.err.push(Status.ERROR.value, folder)
