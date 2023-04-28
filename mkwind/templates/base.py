import os
from pkg_resources import resource_filename
from jinja2 import Template as JinjaTemplate


class Template:
    FILENAME = "job.sh"

    def __init__(self, template_file: os.PathLike):
        with open(template_file, "r") as f:
            self.jtemplate = JinjaTemplate(f.read())

    def render(self, inputs: dict):
        return self.jtemplate.render({"job": inputs})

    def render_to(self, inputs: dict, dst: os.PathLike) -> os.PathLike:
        txt = self.render(inputs)

        if os.path.isdir(dst):
            dst = os.path.join(dst, self.FILENAME)

        with open(dst, "w") as f:
            f.write(txt)

        return dst

    @classmethod
    def from_name(cls, template_name: str):
        if not template_name.endswith(".sh"):
            template_name += ".sh"

        path = resource_filename("mkwind.templates", template_name)

        return cls(path)
