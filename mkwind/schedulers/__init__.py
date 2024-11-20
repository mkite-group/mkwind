from .base import Scheduler, SchedulerJob, SchedulerError
from .slurm import SlurmScheduler
from .pueue import PueueScheduler
from .lsf import LsfScheduler
from .sge import SGEScheduler

SCHEDULERS_CLS = {
    "slurm": SlurmScheduler,
    "pueue": PueueScheduler,
    "lsf": LsfScheduler,
    "sge": SGEScheduler
}
