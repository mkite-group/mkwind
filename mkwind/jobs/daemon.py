import os
import time
from typing import List

from mkwind.user import EnvSettings, Logger
from mkwind.schedulers import Scheduler, SchedulerJob, SchedulerError, SCHEDULERS_CLS
from mkite_core.models import Status
from mkite_engines import EngineRoles, instantiate_from_path


QUEUES = [Status.READY.value, Status.DOING.value, Status.DONE.value, Status.ERROR.value]


class JobDaemon:
    def __init__(
        self,
        scheduler: Scheduler,
        settings: EnvSettings,
        logger_stdout: bool = True,
        error_sleep: int = 120,
    ):
        self.producer = instantiate_from_path(settings.ENGINE_LOCAL, role=EngineRoles.producer)
        self.consumer = instantiate_from_path(settings.ENGINE_LOCAL, role=EngineRoles.consumer)

        self.producer.move = True

        for q in QUEUES:
            self.producer.add_queue(q)

        self.scheduler = scheduler
        self.settings = settings
        self.error_sleep = error_sleep

        log_path = os.path.join(settings.LOG_PATH, "mkwind-run.log")
        self.logger = Logger.to_file(log_path, stdout=logger_stdout)
        self.log("initializing mkwind JobDaemon")

    def log(self, msg: str):
        self.logger.log(msg)

    @classmethod
    def from_settings(cls, settings: EnvSettings, **kwargs):
        scheduler = SCHEDULERS_CLS.get(settings.SCHEDULER)(settings)

        return cls(scheduler, settings, **kwargs)

    def change_status(self, item: str, src_queue: str, dst_queue: str):
        item = self.producer.item_path(src_queue, item)
        dst = self.producer.push(dst_queue, item)
        return dst

    def submit(self):
        n_running = len(self.scheduler.get_running())
        self.logger.log(f"{n_running} jobs running")

        n_pending = len(self.scheduler.get_pending())
        self.logger.log(f"{n_pending} jobs pending")

        n_submit = self.settings.MAX_PENDING - n_pending
        if n_submit > 0:
            self.logger.log(f"{n_submit} slots available in the queue")
            submitted = self.submit_n(n_submit)
            self.logger.log(f"{len(submitted)} jobs submitted")
        else:
            submitted = []
            self.logger.log("no jobs to submit")

        return submitted

    def submit_n(self, n_submit: int):
        submitted = []
        for key, job_folder in self.consumer.get_n(Status.READY.value, n=n_submit):
            dst = self.change_status(job_folder, Status.READY.value, Status.DOING.value)
            job = os.path.basename(dst)

            try:
                self.scheduler.submit_job(dst)
                self.logger.log(f"submitted job {job}")
                submitted.append(job)

            # if there is an error, revert the move operation
            except SchedulerError as e:
                self.change_status(dst, Status.DOING.value, Status.READY.value)
                self.logger.log(f"error submitting {job_folder}: {e}")
                self.logger.log(f"sleeping for {self.error_sleep}")
                time.sleep(self.error_sleep)

        return submitted

    def process_jobs(
        self,
        schedjobs: List[SchedulerJob],
        src: str,
        dst: str,
    ):
        jobs_in_src = self.consumer.list_queue(src)

        processed = []
        for job in schedjobs:
            if job.name in jobs_in_src:
                self.change_status(job.name, src, dst)
                self.logger.log(f"moving {job.name} to {dst}")
                processed.append(job.name)

        return processed

    def process_done(self):
        schedjobs = self.scheduler.get_done()
        done = self.process_jobs(schedjobs, Status.DOING.value, Status.DONE.value)
        self.logger.log(f"{len(done)} jobs done")
        return done

    def process_error(self):
        schedjobs = self.scheduler.get_error()
        errors = self.process_jobs(schedjobs, Status.DOING.value, Status.ERROR.value)
        self.logger.log(f"{len(errors)} jobs terminated with an error")
        return errors

    def process_failed(self):
        schedjobs = self.scheduler.get_failed()
        failed = self.process_jobs(schedjobs, Status.DOING.value, Status.READY.value)
        self.logger.log(f"{len(failed)} jobs failed and will be restarted")
        return failed

    def run(self):
        self.logger.hbar()
        self.logger.log("entering management loop")
        self.process_done()
        self.submit()
        self.process_error()
        self.process_failed()
