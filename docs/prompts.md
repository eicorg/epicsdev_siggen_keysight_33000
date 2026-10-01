## Generate server
Copy this [template](https://github.com/eicorg/epicsdev/blob/main/docs/template.py) to your_module/__main__.py.

Then prompt an AI agent (copilot) following:

```
Modify __main__.py to provide support for Keysight/Agilent 33210A function generator.
Use programming manual from misc/programming_manual.pdf.
Default VISA resource should be `TCPIP::192.168.50.80::INSTR`
```

## Generate Operator Interface (OPI)
Copy this [template](https://github.com/eicorg/epicsdev/blob/main/docs/generate_opi.py) to opi/generate_opi.py.

Then prompt an AI agent (copilot) following:

```
Modify opi/generate_opi.py to support PVs from __main__.py
```
