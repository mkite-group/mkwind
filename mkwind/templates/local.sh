#!/bin/bash -l

{% if job.pre_cmd %}
{{ job.pre_cmd }}
{% endif %}
{{ job.cmd }}
{% if job.post_cmd %}
{{ job.post_cmd }}
{% endif %}