#!/bin/bash -l

{% if job.nodes -%}
#$ -l nodes={{ job.nodes }}
{% endif %}
{%- if job.ntasks -%}
#$ -pe smp {{ job.ntasks }}
{% endif %}
{%- if job.tasks_per_node -%}
#$ -binding linear:{{ job.tasks_per_node }}
{% endif %}
{%- if job.cpus_per_task -%}
#$ -pe smp {{ job.cpus_per_task }}
{% endif %}
{%- if job.gpus_per_task -%}
#$ -l gpu={{ job.gpus_per_task }}
{% endif %}
{%- if job.gpus_per_node -%}
#$ -l gpu_per_node={{ job.gpus_per_node }}
{% endif %}
{%- if job.gres -%}
#$ -l gres={{ job.gres }}
{% endif %}
{%- if job.gpus -%}
#$ -l gpus={{ job.gpus }}
{% endif %}
{%- if job.walltime -%}
#$ -l h_rt={{ job.walltime }}
{% endif %}
{%- if job.partition -%}
#$ -q {{ job.partition }}
{% endif %}
{%- if job.account -%}
#$ -A {{ job.account }}
{% endif %}
{%- if name -%}
#$ -N {{ name }}
#$ -o {{ name }}-$JOB_ID.out
#$ -e {{ name }}-$JOB_ID.error
{% endif %}
{%- if job.memory -%}
#$ -l mem={{ job.memory }}
{% endif %}
{%- if job.memory_per_cpu -%}
#$ -l mem_per_core={{ job.memory_per_cpu }}
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
