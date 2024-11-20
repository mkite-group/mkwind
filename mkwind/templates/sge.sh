#!/bin/bash -l
#$ -cwd
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
#$ -l gpu,cuda={{ job.gpus_per_task }}
{% endif %}
{%- if job.gpus_per_node -%}
#$ -l gpu,cuda={{ job.gpus_per_node }}
{% endif %}
{%- if job.gres -%}
#$ -l gpu,cuda={{ job.gres }}
{% endif %}
{%- if job.gpus -%}
#$ -l gpu,cuda={{ job.gpus }}
{% endif %}
{%- if job.walltime -%}
#$ -l h_rt={{ job.walltime }}
{% endif %}
{%- if job.partition -%}
#$ -l {{ job.partition }}
{% endif %}
{%- if job.account -%}
#$ -A {{ job.account }}
{% endif %}
{%- if name -%}
#$ -N {{ name }}
#$ -o {{ name }}-$JOB_ID.out
#$ -e {{ name }}-$JOB_ID.err
{% endif %}
{%- if job.memory -%}
#$ -l h_vmem={{ job.memory }}
{% endif %}
{%- if job.memory_per_cpu -%}
#$ -l h_data={{ job.memory_per_cpu }}
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
