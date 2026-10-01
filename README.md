# epicsdev_siggen_keysight_33000

EPICS PVAccess server for Keysight/Agilent 33000 series function generators.

The implementation targets the single-channel Keysight/Agilent 33210A and uses
PyVISA for instrument communication.

## Install

```bash
uv sync
```

The package requires Python 3.11 or newer. The installed server command is:

```bash
epicsdev_siggen_keysight_33000
```

## Run

By default, the server connects to
`TCPIP::192.168.50.80::INSTR` and publishes PVs with the prefix
`keysight33000:0:`.

```bash
epicsdev_siggen_keysight_33000
```

Set a different VISA resource, device name, or index with:

```bash
epicsdev_siggen_keysight_33000 \
	--resource 'TCPIP::192.168.50.80::INSTR' \
	--index 0 \
	keysight33000
```

Other options include `--autosave`, `--recall`, `--putlogPV`, and `--verbose`.
Use `--help` for the complete list.

## PVs

Global PVs:

- `visaResource`, `genIDN`, `dateTime`, and `pollCount`
- `instrCmdS` for sending a custom SCPI command
- `instrCmdR` for the command response

Channel 1 PVs:

- `c01Output`, `c01Load`, `c01Polarity`, and `c01WaveType`
- `c01Frequency`, `c01Amplitude`, `c01Offset`, and `c01SquareDuty`
- `c01RampSymmetry`

The server also provides the standard `server`, `status`, `sleep`,
`cycleTime`, `HEARTBEAT`, and `VERSION` PVs from `epicsdev`.

## OPI

Generate the Phoebus display from the repository root with:

```bash
python opi/generate_opi.py
```

This creates `opi/keysight33000.bob`. A different PV prefix or screen title can
be supplied as positional prefix and `--title` arguments:

```bash
python opi/generate_opi.py --title 'Keysight 33000' 'pva://keysight33000:0:'
```


