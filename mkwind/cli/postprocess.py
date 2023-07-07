import sys
import time
import click

from mkwind.user.settings import get_settings
from mkwind.postprocess import PostprocessDaemon


@click.command("postprocess")
@click.option(
    "-s",
    "--settings",
    type=str,
    default=None,
    help="path to the settings.yaml file configuring the mkwind runner",
)
@click.option(
    "-l",
    "--sleep",
    type=int,
    default=60,
    help="number of seconds to sleep between runs of the daemon",
)
@click.option(
    "-r",
    "--allow_restart",
    is_flag=True,
    default=False,
    help="If set, allows restarting jobs on postprocessing",
)
def postprocess(settings, sleep, allow_restart=False):
    daemon = PostprocessDaemon.from_settings(
        settings=get_settings(settings),
        allow_restart=allow_restart,
    )

    if sleep <= 0:
        daemon.log("running only once, as sleep <= 0")
        daemon.run()
        daemon.log("exiting")
        sys.exit()

    while True:
        daemon.run()
        daemon.log(f"sleeping for {sleep} seconds")
        time.sleep(sleep)
