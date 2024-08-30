import os

from mkite_core.models import Status
from mkite_engines import EngineRoles, instantiate_from_path
from mkwind.user import EnvSettings, Logger
from mkwind.templates import Template

from .base import JobBuilder


class BuilderDaemon:
    def __init__(
        self,
        builder: JobBuilder,
        settings: EnvSettings,
        logger_stdout: bool = True,
    ):
        self.builder = builder
        self.settings = settings

        log_path = os.path.join(settings.LOG_PATH, "mkwind-build.log")
        self.logger = Logger.to_file(log_path, stdout=logger_stdout)
        self.log("initializing mkwind BuilderDaemon")

    def log(self, msg: str):
        self.logger.log(msg)

    def build(self):
        self.log("building new jobs")
        num_ready = self.builder.get_ready()
        num_to_build = self.settings.MAX_READY - num_ready

        if num_to_build > 0:
            built = self.builder.build_all(max_build=num_to_build)
            self.log(f"built {len(built)} new jobs")
            return built

        self.log("skipping building jobs")
        return []

    def run(self):
        self.logger.hbar()
        self.log("entering management loop")
        self.build()

    @classmethod
    def from_settings(
        cls,
        settings: EnvSettings,
        logger_stdout: bool = True,
        explicit_config: bool = True,
        delete_on_build: bool = False,
    ):
        src = instantiate_from_path(settings.ENGINE_EXTERNAL, role=EngineRoles.consumer)
        dst = instantiate_from_path(settings.ENGINE_LOCAL, role=EngineRoles.producer)
        dst.add_queue(Status.READY)

        template = Template.from_name(settings.SCHEDULER)

        builder = JobBuilder(
            src_engine=src,
            dst_engine=dst,
            settings=settings,
            template=template,
            explicit_config=explicit_config,
            delete_on_build=delete_on_build,
        )
        return cls(builder, settings, logger_stdout=logger_stdout)
