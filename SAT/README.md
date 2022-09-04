# VLSI solving using SAT
Two main encodings were tested (more info in the report): direct and order encodings. `SAT_model.py` and `SAT_model_rotations.py` implement direct encoding
models (respectively without and with rotations). `SAT_model_order` and `SAT_model_order_rotations` implement order encoding models.

## Execution
`exec_all.py` feeds instances to the models. Make sure that `DEFAULT_INSTANCES_DIR` constant is properly set to find json instances files (if no files have been touched, it is correctly configured).

To execute the direct encoding model without rotations:
```bash
python exec_all.py
```

To execute the direct encoding model with rotations:
```bash
python exec_all.py -r
```

To execute the order encoding model without rotations:
```bash
python exec_all.py -o
```

To execute the order encoding model with rotations:
```bash
python exec_all.py -or
```
