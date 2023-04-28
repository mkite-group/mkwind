import click

from mkwind.cli.builder import build
from mkwind.cli.build_one import build_one
from mkwind.cli.postprocess import postprocess
from mkwind.cli.runner import run


class WindGroup(click.Group):
    pass


@click.command(cls=WindGroup)
def wind():
    """Command line interface for mkwind"""


wind.add_command(build)
wind.add_command(build_one)
wind.add_command(postprocess)
wind.add_command(run)


if __name__ == "__main__":
    wind()
