# VLSI solving using constraint programming
`final_rotation.mzn` is the reference model for solutions that admit rotations. `final.mzn` is the reference model for solutions without rotations.

`naive.mzn` was included for completeness, the name says it all.

## Execution
`exec_all.py` feeds instances to the models. Make sure that `DEFAULT_INSTANCES_DIR` constant is properly set to find json instances files (if no files have been touched, it is correctly configured).

To execute the rotation aware model:
```bash
python exec_all.py -r
```
To execute the rotation unaware model:
```bash
python exec_all.py
```
