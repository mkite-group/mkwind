#!/bin/bash -l
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=36
#SBATCH --time=30:00
#SBATCH --partition=pdebug
#SBATCH --account=test

module load vasp
srun -n$SLURM_NTASKS vasp
touch mkwind-complete
