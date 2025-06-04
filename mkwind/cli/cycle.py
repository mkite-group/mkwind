import os

import click
from mkite_core.models import JobInfo, Status
from mkite_core.plugins import get_recipe
from mkite_engines import EngineRoles, instantiate_from_path
from mkite_engines.local import LocalConsumer, LocalProducer
from mkwind.builder import JobBuilder
from mkwind.postprocess import JobPostprocessor
from mkwind.templates import Template
from mkwind.user.settings import get_settings


@click.command("cycle")
@click.argument("recipe", type=str)
@click.option(
    "-s",
    "--settings",
    type=str,
    default=None,
    help="path to the settings.yaml file configuring the mkwind builder",
)
@click.option(
    "-d",
    "--dst",
    type=str,
    default=".",
    help="path to the destination folder where the job will be built",
)
def cycle(recipe, settings, dst):
    return _cycle(recipe, settings, dst)


def _cycle(recipe, settings, dst):
    settings, builder, pproc = _get_managers(settings, dst)
    _run_cycle(builder, pproc, recipe)


def _get_managers(settings, dst):
    settings = get_settings(settings)

    # Prep: initiate the builder
    src_engine = instantiate_from_path(
        settings.ENGINE_EXTERNAL, role=EngineRoles.consumer
    )
    dst_engine = LocalProducer(root_path=dst)
    dst_engine.add_queue(Status.READY)

    template = Template.from_name(settings.SCHEDULER)

    builder = JobBuilder(
        src_engine=src_engine,
        dst_engine=dst_engine,
        settings=settings,
        template=template,
        explicit_config=True,
        delete_on_build=True,
    )

    # Prep: initiate the postprocessor
    pproc_dst = instantiate_from_path(
        settings.ENGINE_EXTERNAL, role=EngineRoles.producer
    )
    pproc_src = LocalConsumer(root_path=dst)

    err = instantiate_from_path(settings.ENGINE_LOCAL, role=EngineRoles.producer)
    err.add_queue(Status.ERROR)

    arch = instantiate_from_path(settings.ENGINE_ARCHIVE, role=EngineRoles.producer)
    arch.add_queue(Status.ARCHIVE)

    pproc = JobPostprocessor(
        src_engine=pproc_src,
        dst_engine=pproc_dst,
        error_engine=err,
        archive_engine=arch,
        compress=True,
        allow_restart=False,
    )

    return settings, builder, pproc


def _run_cycle(builder, pproc, recipe):
    # 1. Builds the job onto a new folder
    key, info, folder = builder.build_one(recipe)

    if folder is None or info is None:
        return

    # 2. Run the job at that folder
    cwd = os.getcwd()
    os.chdir(folder)

    try:
        RecipeCls = get_recipe(recipe).load()
        job = RecipeCls(info)
        job.run()
    except Exception as e:
        print(f"ERROR: Failed to run the job {info.job}")
        print(f"ERROR: {e}")

    # 3. Postprocess the folder
    os.chdir(cwd)

    try:
        pproc.postprocess_one(folder)
    except Exception as e:
        print(f"ERROR: Failed to postprocess the job {info.job}")
        print(f"ERROR: {e}")

    return
