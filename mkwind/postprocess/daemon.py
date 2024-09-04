import os

from mkwind.user import EnvSettings, Logger
from mkite_core.models import Status
from mkite_engines import EngineRoles, instantiate_from_path

from .base import JobPostprocessor


class PostprocessDaemon:
    def __init__(
        self,
        postproc: JobPostprocessor,
        settings: EnvSettings,
        logger_stdout: bool = True,
    ):
        self.settings = settings
        self.postproc = postproc

        log_path = os.path.join(settings.LOG_PATH, "mkwind-postproc.log")
        self.logger = Logger.to_file(log_path, stdout=logger_stdout)
        self.log("initializing mkwind PostprocessDaemon")

    def log(self, msg: str):
        self.logger.log(msg)

    def postprocess(self):
        done, errors = self.postproc.postprocess_all()
        return done, errors

    def run(self):
        self.logger.hbar()
        self.log("postprocessing jobs")
        done, errors = self.postprocess()
        self.log(f"{len(done)} jobs postprocessed")
        self.log(f"{len(errors)} jobs with errors")

    @classmethod
    def from_settings(
        cls,
        settings: EnvSettings,
        compress: bool = True,
        allow_restart: bool = False,
        logger_stdout: bool = True,
    ):
        src = instantiate_from_path(settings.ENGINE_LOCAL, role=EngineRoles.consumer)
        src.add_queue(Status.DONE)

        dst = instantiate_from_path(settings.ENGINE_EXTERNAL, role=EngineRoles.producer)
        dst.add_queue(Status.PARSING)

        err = instantiate_from_path(settings.ENGINE_LOCAL, role=EngineRoles.producer)
        err.add_queue(Status.ERROR)

        arch = instantiate_from_path(settings.ENGINE_ARCHIVE, role=EngineRoles.producer)
        arch.add_queue(Status.ARCHIVE)

        postproc = JobPostprocessor(
            src_engine=src,
            dst_engine=dst,
            error_engine=err,
            archive_engine=arch,
            compress=compress,
            allow_restart=allow_restart,
        )
        return cls(postproc, settings, logger_stdout=logger_stdout)
