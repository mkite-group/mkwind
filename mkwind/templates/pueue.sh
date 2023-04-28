#!/bin/bash -l

{% if job.pre_cmd %}
{{ job.pre_cmd }}
{% endif %}
{%- if job.cmd -%}
{{ job.cmd }}
{% endif %}
{%- if job.post_cmd -%}
{{ job.post_cmd }}
{% endif %}
