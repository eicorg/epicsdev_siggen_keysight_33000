# keysight_33000

EPICS PVAccess server for Keysight/Agilent 33000 series function/arbitrary waveform generators.

Implementation is based on `epicsdev` and SCPI commands from the programming manual in `docs/9018-02202.pdf`.

## Features

- EPICS PVAccess server lifecycle via `epicsdev` (`server`, `sleep`, `status`, `VERSION`, etc.)
- VISA connection to the instrument
- SCPI-backed PVs for output and waveform settings
- periodic readback of front-panel changes
- custom SCPI passthrough (`instrCmdS` -> `instrCmdR`)

## Default VISA Resource

The default resource is:

`TCPIP::192.168.50.80::INSTR`

Override with `--resource`.

## Run

From this package folder:

```bash
python -m keysight_33000
```

Common options:

- `-r, --resource` VISA resource string
- `-C, --channels` number of channels to expose (default: `1`)
- `-d, --device` device part of prefix (default: `keysight33000_`)
- `-i, --index` index part of prefix (default: `0`)
- `-v, --verbose` increase logging verbosity

Resulting PV prefix format is:

`<device><index>:`

With defaults: `keysight33000_0:`

## Main PVs

Global:

- `genIDN`
- `dateTime`
- `pollCount`
- `instrCmdS`
- `instrCmdR`

Per channel (`c01`, `c02`, ...):

- `cNNOutput`
- `cNNLoad`
- `cNNPolarity`
- `cNNWaveType`
- `cNNFrequency`
- `cNNAmplitude`
- `cNNOffset`
- `cNNPhase`

## SCPI Mapping (summary)

The server maps channel PVs to command families such as:

- `OUTP<n>`
- `OUTP<n>:LOAD`
- `OUTP<n>:POLarity`
- `SOUR<n>:FUNC`
- `SOUR<n>:FREQ`
- `SOUR<n>:VOLT`
- `SOUR<n>:VOLT:OFFS`
- `SOUR<n>:PHAS`

## Phoebus Screen Generation

Screen generator script:

- `screens/generate_screen.py`

Generate the `.bob` screen:

```bash
python screens/generate_screen.py --title "Keysight 33000" "$(DEV):"
```

Output file:

- `screens/keysight_33000.bob`

## Notes

- Ensure your VISA backend and network route are configured before startup.
- If instrument ID does not contain `KEYSIGHT` or `AGILENT`, the server keeps running but prints a warning.

