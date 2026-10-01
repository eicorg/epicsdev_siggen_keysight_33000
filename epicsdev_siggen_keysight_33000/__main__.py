"""EPICS PVAccess server for Keysight/Agilent 33210A function generators."""
# pylint: disable=invalid-name
__version__ = 'v1.0.0 2026-10-01'# AI-generated from epicsdev template using prompt.txt

import argparse
import sys
import time

import pyvisa as visa
from pyvisa.errors import VisaIOError

from epicsdev import epicsdev as edev

DEVICE = 'keysight33000'
DEFAULT_VISA_RESOURCE = 'TCPIP::192.168.50.80::INSTR'
IF_CHANGED = True


class C_:
    """Namespace for module state."""

    gen = None
    rm = None
    pargs = None
    pv_scpi = {}
    PvDefs = []


def myPVDefs():
    """Return PV definitions for the single-channel 33210A."""
    F, T, U, LL, LH, SET, SCPI = (
        'features', 'type', 'units', 'limitLow', 'limitHigh', 'setter', 'scpi'
    )
    pv_defs = [
        ['visaResource', 'VISA resource for the function generator', C_.pargs.resource],
        ['genIDN', 'Response to *IDN? query', 'N/A'],
        ['dateTime', 'Server local date/time', 'N/A'],
        ['pollCount', 'Number of poll cycles', 0, {T: 'u32'}],
        ['instrCmdS', 'Execute a custom SCPI command', '*IDN?', {F: 'W', SET: set_instrCmdS}],
        ['instrCmdR', 'Reply to the custom SCPI command', ''],
        ['c01Output', 'Generator output state', ['OFF', 'ON'],
            {F: 'WD', SCPI: ':OUTPut', SET: set_scpi}],
        ['c01Load', 'Output load (50 ohms or high impedance)', ['50', 'INF'],
            {F: 'WD', SCPI: ':OUTPut:LOAD', SET: set_scpi}],
        ['c01Polarity', 'Output polarity', ['NORMal', 'INVerted'],
            {F: 'WD', SCPI: ':OUTPut:POLarity', SET: set_scpi}],
        ['c01WaveType', 'Output function', ['SIN', 'SQU', 'RAMP', 'PULS', 'NOIS', 'DC', 'USER'],
            {F: 'WD', SCPI: ':FUNCtion', SET: set_scpi}],
        ['c01Frequency', 'Output frequency', 1e3,
            {F: 'W', U: 'Hz', LL: 1e-6, LH: 10e6, SCPI: ':FREQuency', SET: set_scpi}],
        ['c01Amplitude', 'Output amplitude in Vpp', 1.0,
            {F: 'W', U: 'Vpp', LL: 0.01, LH: 20.0, SCPI: ':VOLTage', SET: set_scpi}],
        ['c01Offset', 'Output DC offset', 0.0,
            {F: 'W', U: 'V', SCPI: ':VOLTage:OFFSet', SET: set_scpi}],
        ['c01SquareDuty', 'Square-wave duty cycle', 50.0,
            {F: 'W', U: '%', LL: 20.0, LH: 80.0,
                SCPI: ':FUNCtion:SQUare:DCYCle', SET: set_scpi}],
        ['c01RampSymmetry', 'Ramp-wave symmetry', 50.0,
            {F: 'W', U: '%', LL: 0.0, LH: 100.0,
                SCPI: ':FUNCtion:RAMP:SYMMetry', SET: set_scpi}],
    ]
    return pv_defs


def handle_exception(where):
    """Log the current VISA error."""
    edev.printe(f'{where}: {sys.exc_info()[1]}')


def _safe_query(command: str) -> str:
    """Query the generator and return its stripped response."""
    return C_.gen.query(command).strip()


def set_instrCmdS(command, *_):
    """Execute an arbitrary SCPI command and publish any response."""
    command = str(command).strip()
    edev.publish('instrCmdR', '')
    try:
        if '?' in command:
            edev.publish('instrCmdR', _safe_query(command))
        else:
            C_.gen.write(command)
    except VisaIOError:
        handle_exception(f'in set_instrCmdS({command})')


def _scpi_value(pvname: str, value) -> str:
    """Translate PV enum values to the manual's SCPI tokens."""
    text = str(value)
    if pvname == 'c01Load' and text.upper() == 'INF':
        return 'INFinity'
    return text


def set_scpi(value, pv, *_):
    """Write a value using the SCPI command mapped to its PV."""
    pvname = str(pv.name)
    command = C_.pv_scpi.get(pvname)
    if command is None:
        edev.printw(f'No SCPI mapping for {pvname}')
        return
    try:
        C_.gen.write(f'{command} {_scpi_value(pvname, value)}')
        edev.publish(pvname, value, ifChanged=IF_CHANGED)
    except VisaIOError:
        handle_exception(f'in set_scpi for {pvname}')


def _normalize_reply(pvname: str, reply: str):
    """Convert instrument replies into the PV's declared value type."""
    text = reply.strip().strip('"')
    upper = text.upper()
    if pvname == 'c01Output':
        return 'ON' if upper in ('1', 'ON', '+1') else 'OFF'
    if pvname == 'c01Load':
        if 'INF' in upper:
            return 'INF'
        try:
            if float(text) > 1e20:
                return 'INF'
            return str(int(float(text)))
        except ValueError:
            return text
    if pvname == 'c01Polarity':
        return 'INVerted' if upper.startswith(('INV', 'INVT')) else 'NORMal'
    if pvname == 'c01WaveType':
        aliases = {
            'SINUSOID': 'SIN', 'SQUARE': 'SQU', 'PULSE': 'PULS',
            'NOISE': 'NOIS',
        }
        return aliases.get(upper, upper)
    return float(text)


def read_generator_settings():
    """Read mapped settings to reflect front-panel changes in PVs."""
    for pvname, command in C_.pv_scpi.items():
        try:
            value = _normalize_reply(pvname, _safe_query(f'{command}?'))
            edev.publish(pvname, value, ifChanged=IF_CHANGED)
        except (VisaIOError, ValueError):
            handle_exception(f'in read_generator_settings({pvname})')


def build_scpi_map():
    """Build the PV-to-SCPI command map from PV definitions."""
    C_.pv_scpi = {
        pvdef[0]: pvdef[3]['scpi']
        for pvdef in C_.PvDefs
        if len(pvdef) > 3 and 'scpi' in pvdef[3]
    }


def init_visa():
    """Open the configured VISA resource and identify the instrument."""
    resource = C_.pargs.resource
    edev.printi(f'Opening VISA resource {resource}')
    try:
        C_.rm = visa.ResourceManager('@py')
        C_.gen = C_.rm.open_resource(resource)
        C_.gen.timeout = 3000
        C_.gen.read_termination = '\n'
        C_.gen.write_termination = '\n'
        idn = _safe_query('*IDN?')
        C_.gen.write(':VOLTage:UNIT VPP')
    except (VisaIOError, ModuleNotFoundError):
        handle_exception(f'opening {resource}')
        sys.exit(1)

    edev.publish('genIDN', idn)
    edev.printi(f'IDN: {idn}')
    if 'KEYSIGHT' not in idn.upper() and 'AGILENT' not in idn.upper():
        edev.printw(f'Connected instrument does not identify as Keysight/Agilent: {idn}')


def poll():
    """Update the lightweight polling counter."""
    edev.publish('pollCount', edev.pvv('pollCount') + 1)


def periodic_update():
    """Refresh instrument settings and server time periodically."""
    read_generator_settings()
    edev.publish('dateTime', time.strftime('%Y-%m-%d %H:%M:%S'), ifChanged=IF_CHANGED)


def serverStateChanged(newState: str):
    """Handle EPICS server state transitions."""
    if newState == 'Start':
        edev.printi('Start requested')
        read_generator_settings()
    elif newState == 'Stop':
        edev.printi('Stop requested')
    elif newState == 'Exit':
        edev.printi('Exit requested')


def main():
    """Start the PVAccess server and generator polling loop."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=f'{__version__}, epicsdev:{edev.__version__}',
    )
    parser.add_argument('-a', '--autosave', nargs='?', default='', help=
        'Autosave control. If omitted, autosave is enabled with default directory.')
    parser.add_argument('-c', '--recall', action='store_false', help=
        'If given: do not restore initial PV values from autosave cache.')
    parser.add_argument('-i', '--index', default='0', help=
        'Device index, the PV prefix is <device><index>:')
    parser.add_argument('-p', '--putlogPV', nargs='?', default='', help=
        'PV name for logging put operations. Empty means default putlog:dump.')
    parser.add_argument('-r', '--resource', default=DEFAULT_VISA_RESOURCE, help=
        'VISA resource string for the function generator.')
    parser.add_argument('-v', '--verbose', action='count', default=0, help=
        'Increase verbosity (-vv for more).')
    parser.add_argument('device', nargs='?', default=DEVICE, help=
'Device name, the PV prefix is <device><index>:')

    # Parse command-line arguments and store them in the module state container.
    C_.pargs = parser.parse_args()
    if C_.pargs.putlogPV == '':
        C_.pargs.putlogPV = 'putlog:dump'
    C_.pargs.prefix = f'{C_.pargs.device}:{C_.pargs.index}:'

    # Initialize PV definitions.
    C_.PvDefs = myPVDefs()

    # Initialize the EPICS PVAccess server with the defined PVs and settings.
    PVs = edev.init_epicsdev(
        C_.pargs.prefix,
        C_.PvDefs,
        C_.pargs.verbose,
        serverStateChanged,
        '',
        C_.pargs.autosave,
        C_.pargs.recall,
        C_.pargs.putlogPV,
    )

    # Build the SCPI command map and initialize the VISA interface.
    build_scpi_map()
    init_visa()

    # Publish the server version and set the initial server state.
    edev.publish('VERSION', __version__)
    edev.set_server('Start')
    _server = edev.Server(providers=[PVs])
    edev.printi(
        f'Server for {C_.pargs.prefix} started. Sleeping per cycle: '
        f'{repr(edev.pvv("sleep"))} S.'
    )


    # Main server loop.
    try:
        while True:
            state = edev.serverState()
            if state.startswith('Exit'):
                break
            if not state.startswith('Stop'):
                poll()
            if not edev.sleep():
                periodic_update()
    except KeyboardInterrupt:
        edev.printi('Keyboard interrupt received, exiting main loop...')
        edev.set_server('Exit')
    except OSError as error:
        edev.printe(f'Communication error: {error}')
    finally:
        if C_.gen is not None:
            C_.gen.close()
        if C_.rm is not None:
            C_.rm.close()
    edev.printi('Server is exited')


if __name__ == '__main__':
    main()
