#!/bin/bash -l

{% if job.nodes -%}
#SBATCH --nodes={{ job.nodes }}
{% endif %}
{%- if job.ntasks -%}
#SBATCH --ntasks={{ job.ntasks }}
{% endif %}
{%- if job.tasks_per_node -%}
#SBATCH --ntasks-per-node={{ job.tasks_per_node }}
{% endif %}
{%- if job.cpus_per_task -%}
#SBATCH --cpus-per-task={{ job.cpus_per_task }}
{% endif %}
{%- if job.gpus_per_task -%}
#SBATCH --gpus-per-task={{ job.gpus_per_task }}
{% endif %}
{%- if job.gpus_per_node -%}
#SBATCH --gpus-per-node={{ job.gpus_per_node }}
{% endif %}
{%- if job.gres -%}
#SBATCH --gres={{ job.gres }}
{% endif %}
{%- if job.gpus -%}
#SBATCH --gpus={{ job.gpus }}
{% endif %}
{%- if job.walltime -%}
#SBATCH --time={{ job.walltime }}
{% endif %}
{%- if job.partition -%}
#SBATCH --partition={{ job.partition }}
{% endif %}
{%- if job.account -%}
#SBATCH --account={{ job.account }}
{% endif %}
{%- if name -%}
#SBATCH --job-name={{ name }}
#SBATCH --output={{ name }}-%j.out
#SBATCH --error={{ name }}-%j.error
{% endif %}
{%- if job.memory -%}
#SBATCH --mem={{ job.memory }}
{% endif %}
{%- if job.memory_per_cpu -%}
#SBATCH --mem-per-cpu={{ job.memory_per_cpu }}
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
