import sys
import time
import click

from mkwind.builder import BuilderDaemon
from mkwind.user.settings import get_settings


@click.command("build")
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
    "-e",
    "--explicit",
    is_flag=True,
    default=False,
    help="If True, requires recipe config/package to be explicit in \
        the config file. This helps separating which recipes will be \
        built in different machines.",
)
def build(settings, sleep, explicit=False):
    daemon = BuilderDaemon.from_settings(
        settings=get_settings(settings),
        explicit_config=explicit,
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
