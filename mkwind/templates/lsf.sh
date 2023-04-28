#!/bin/bash -l

{% if job.nodes -%}
#BSUB -nnodes {{ job.nodes }}
{% endif %}
{%- if job.ntasks -%}
#BSUB -n {{ job.ntasks }}
{% endif %}
{%- if job.walltime -%}
#BSUB -W {{ job.walltime }}
{% endif %}
{%- if job.partition -%}
#BSUB -q {{ job.partition }}
{% endif %}
{%- if job.account -%}
#BSUB -G {{ job.account }}
{% endif %}
{%- if name -%}
#BSUB -J {{ name }}
#BSUB -o {{ name }}-%j.out
#BSUB -e {{ name }}-%j.error
{% endif %}
{%- if job.memory -%}
#BSUB -M {{ job.memory }}
{% endif %}

{%- if job.pre_cmd -%}
{{ job.pre_cmd }}
{% endif %}
{%- if job.cmd -%}
{{ job.cmd }}
{% endif %}
{%- if job.post_cmd -%}
{{ job.post_cmd }}
{% endif %}
