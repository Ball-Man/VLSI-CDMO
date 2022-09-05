# Combinatorial approaches for the VLSI problem
A variety of scripts have been used to ease the pain of dealing with three different models.

## Projects structure
Each approach is descripted in its own director (CP, SAT, MIP). An SMT model is included even if incomplete. All the models are executed on all instances by using `exec_all` scripts (on of them is present in each directory).

Said scripts feed the models with a json representation of the forty given instances (found in `instances_json/`).

### Converting instances
`instances_json` is computed by the `convert_instances` script:
```bash
python convert_instances.py instances
```
The script also includes a `max_height` approximation obtained with a naive first fit algorithm (module `first_fit.py`).

### Visualization
To ensure that an instance is correct, `visualize_solution` can be used:
```bash
python visualize_solution.py solution_file.txt
```
Plots in the report were obtained by using the `barplot` script. `python barplot.py -h` to know more.


## Requirements
Python >= 3.8
Python packages (can be found in `requirements.txt`:
* *pyglet* (visualization)
* *minizinc* (constraint programming)
* *gurobipy* (mixed integer programming)
* *pulp*	(mixed integer programming)
* *z3-solver (SAT)
* *matplotlib* (plots)
* *numpy* (plots)
Minizinc IDE >= 2.6.X (IDE version installs the necessary solvers, also on linux)

### Python requirements via pip
```bash
pip install --user -r requirements.txt
```
