from .base import Scheduler, SchedulerJob, SchedulerError
from .slurm import SlurmScheduler
from .pueue import PueueScheduler
from .lsf import LsfScheduler
from .sge import SGEScheduler
from .local import LocalScheduler

SCHEDULERS_CLS = {
    "slurm": SlurmScheduler,
    "pueue": PueueScheduler,
    "lsf": LsfScheduler,
    "sge": SGEScheduler,
    "local": LocalScheduler
}
