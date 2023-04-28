import click

from mkite_core.models import JobInfo
from mkite_engines.local import LocalProducer
from mkwind.user.settings import get_settings
from mkwind.builder import JobBuilder
from mkwind.templates import Template, TEMPLATE_FILES


@click.command("build_one")
@click.option(
    "-i",
    "--info",
    type=str,
    default="jobinfo.json",
    help="path to the jobinfo.json that should be built",
)
@click.option(
    "-s",
    "--settings",
    type=str,
    default=None,
    help="path to the settings.yaml file configuring the mkwind builder",
)
@click.option(
    "-t",
    "--template",
    default=None,
    type=click.Choice(TEMPLATE_FILES, case_sensitive=True),
    help="name of the template to be used when building the jobs.\
        If not given, will use the default template in the settings",
)
@click.option(
    "-d",
    "--dst",
    type=str,
    default=".",
    help="path to the destination folder where the job will be built",
)
def build_one(info, settings, template, dst):
    info = JobInfo.from_json(info)

    _settings = get_settings(settings)

    template = _settings.SCHEDULER if template is None else template
    _template = Template.from_name(template)
    _dst = LocalProducer(root_path=dst)

    builder = JobBuilder(None, _dst, _settings, _template)
    builder.build_job(info)
