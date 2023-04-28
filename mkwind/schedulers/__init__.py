from .base import Scheduler, SchedulerJob, SchedulerError
from .slurm import SlurmScheduler
from .pueue import PueueScheduler
from .lsf import LsfScheduler

SCHEDULERS_CLS = {
    "slurm": SlurmScheduler,
    "pueue": PueueScheduler,
    "lsf": LsfScheduler
}
