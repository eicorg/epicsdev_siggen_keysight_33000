"""EPICS PVAccess server for Keysight 33000 signal generators."""
# pylint: disable=invalid-name
__version__ = 'v0.1.0 26-08-26'

import argparse
from dataclasses import dataclass
import re
import sys
import time

import pyvisa as visa
from pyvisa.errors import VisaIOError

from epicsdev import epicsdev as edev

DEFAULT_VISA_RESOURCE = 'TCPIP::192.168.50.80::INSTR'
DEFAULT_CHANNELS = 1
IF_CHANGED = True
pargs = None


@dataclass(slots=True)
class C_:
    """Namespace for module state."""

    gen = None
    pv_scpi = {}
    PvDefs = []


def _ch_from_pv(pvname: str) -> int:
    """Return channel index from PV name cNN..."""
    m = re.match(r'c(\d{2})', pvname)
    if m is None:
        raise ValueError(f'Cannot parse channel from PV name {pvname}')
    return int(m.group(1))


def _parse_first_number(text: str):
    """Parse first float-like token from a SCPI value string."""
    m = re.search(r'[-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?', str(text))
    return float(m.group(0)) if m else None


def _safe_query(cmd: str):
    """Run SCPI query and return stripped response."""
    return C_.gen.query(cmd).strip()


def _safe_write(cmd: str):
    """Run SCPI command."""
    C_.gen.write(cmd)


def handle_exception(where):
    """Log exception with location."""
    edev.printe(f'{where}: {sys.exc_info()[1]}')


def set_instrCmdS(cmd, *_):
    """Execute arbitrary SCPI command from PV."""
    cmd = str(cmd).strip()
    edev.publish('instrCmdR', '')
    try:
        if '?' in cmd:
            r = _safe_query(cmd)
            edev.publish('instrCmdR', r)
        else:
            _safe_write(cmd)
    except VisaIOError:
        handle_exception(f'in set_instrCmdS({cmd})')


def _set_scpi(value, pv, suffix: str):
    """Write a channel-specific SCPI command based on PV name."""
    pvname = str(pv.name)
    _ = _ch_from_pv(pvname)  # Validate naming cNN...
    cmd = C_.pv_scpi.get(pvname)
    if cmd is None:
        edev.printw(f'No SCPI mapping for {pvname}')
        return
    try:
        _safe_write(f'{cmd}{suffix}{value}')
        edev.publish(pvname, value, ifChanged=IF_CHANGED)
    except VisaIOError:
        handle_exception(f'in _set_scpi for {pvname}')


def set_output(value, pv, *_):
    """Setter for channel output ON/OFF."""
    v = 'ON' if str(value).upper() in ('1', 'ON', 'TRUE') else 'OFF'
    _set_scpi(v, pv, ' ')


def set_load(value, pv, *_):
    """Setter for channel output load (50/INF)."""
    v = str(value).upper()
    if v in ('HZ', 'INFINITY'):
        v = 'INF'
    _set_scpi(v, pv, ' ')


def set_polarity(value, pv, *_):
    """Setter for channel output polarity."""
    v = str(value).upper()
    if v == 'NORM':
        v = 'NORMal'
    elif v == 'INV':
        v = 'INVerted'
    _set_scpi(v, pv, ' ')


def set_wave_type(value, pv, *_):
    """Setter for waveform function."""
    _set_scpi(str(value).upper(), pv, ' ')


def set_frequency(value, pv, *_):
    """Setter for frequency."""
    _set_scpi(value, pv, ' ')


def set_amplitude(value, pv, *_):
    """Setter for amplitude."""
    _set_scpi(value, pv, ' ')


def set_offset(value, pv, *_):
    """Setter for offset."""
    _set_scpi(value, pv, ' ')


def set_phase(value, pv, *_):
    """Setter for phase."""
    _set_scpi(value, pv, ' ')


def myPVDefs():
    """PV definitions for Keysight 33000 generators.

    Commands are based on programming manual 9018-02202.
    """
    F, T, U, LL, LH, SET, SCPI = 'features', 'type', 'units', 'limitLow', 'limitHigh', 'setter', 'scpi'

    pvDefs = [
        ['visaResource', 'VISA resource used to access the signal generator', pargs.resource],
        ['genIDN', 'Response to *IDN? query', 'N/A'],
        ['dateTime', 'Server local date/time', 'N/A'],
        ['pollCount', 'Number of poll cycles', 0, {T: 'u32'}],
        ['instrCmdS', 'Execute custom SCPI command', '*IDN?', {F: 'W', SET: set_instrCmdS}],
        ['instrCmdR', 'Reply to custom SCPI command', ''],
    ]

    channelTemplates = [
        ['c<n>Output', 'Channel output state', ['OFF', 'ON'],
            {F: 'WD', SCPI: 'OUTP<n>', SET: set_output}],
        ['c<n>Load', 'Output load', ['50', 'INF'],
            {F: 'WD', SCPI: 'OUTP<n>:LOAD', SET: set_load}],
        ['c<n>Polarity', 'Output polarity', ['NORMal', 'INVerted'],
            {F: 'WD', SCPI: 'OUTP<n>:POLarity', SET: set_polarity}],
        ['c<n>WaveType', 'Waveform function (FUNC)',
            ['SIN', 'SQU', 'RAMP', 'PULS', 'NOIS', 'DC', 'ARB'],
            {F: 'WD', SCPI: 'SOUR<n>:FUNC', SET: set_wave_type}],
        ['c<n>Frequency', 'Frequency', 1e3,
            {F: 'W', U: 'Hz', LL: 1e-6, LH: 120e6, SCPI: 'SOUR<n>:FREQ', SET: set_frequency}],
        ['c<n>Amplitude', 'Amplitude Vpp', 1.0,
            {F: 'W', U: 'Vpp', LL: 0.001, LH: 20.0, SCPI: 'SOUR<n>:VOLT', SET: set_amplitude}],
        ['c<n>Offset', 'DC offset voltage', 0.0,
            {F: 'W', U: 'V', LL: -10.0, LH: 10.0, SCPI: 'SOUR<n>:VOLT:OFFS', SET: set_offset}],
        ['c<n>Phase', 'Phase angle', 0.0,
            {F: 'W', U: 'deg', LL: -360.0, LH: 360.0, SCPI: 'SOUR<n>:PHAS', SET: set_phase}],
    ]

    for ch in range(pargs.channels):
        for pvdef in channelTemplates:
            p = pvdef.copy()
            p[0] = p[0].replace('<n>', f'{ch + 1:02d}')
            p[3] = p[3].copy()
            p[3][SCPI] = p[3][SCPI].replace('<n>', str(ch + 1))
            pvDefs.append(p)
    return pvDefs


def read_channel_settings(ch: int):
    """Read channel settings from device and publish corresponding PVs."""
    try:
        outp = _safe_query(f'OUTP{ch}?').strip()
        load = _safe_query(f'OUTP{ch}:LOAD?').strip()
        pol = _safe_query(f'OUTP{ch}:POLarity?').strip()
        func = _safe_query(f'SOUR{ch}:FUNC?').strip()
        freq = _safe_query(f'SOUR{ch}:FREQ?').strip()
        ampl = _safe_query(f'SOUR{ch}:VOLT?').strip()
        offs = _safe_query(f'SOUR{ch}:VOLT:OFFS?').strip()
        phas = _safe_query(f'SOUR{ch}:PHAS?').strip()

        edev.publish(f'c{ch:02d}Output', 'ON' if outp in ('1', 'ON') else 'OFF', ifChanged=IF_CHANGED)

        lv = _parse_first_number(load)
        load_pv = 'INF' if (lv is not None and lv > 1e36) or 'INF' in load.upper() else '50'
        edev.publish(f'c{ch:02d}Load', load_pv, ifChanged=IF_CHANGED)

        if pol.upper().startswith('INV'):
            pol = 'INVerted'
        else:
            pol = 'NORMal'
        edev.publish(f'c{ch:02d}Polarity', pol, ifChanged=IF_CHANGED)

        edev.publish(f'c{ch:02d}WaveType', func.upper(), ifChanged=IF_CHANGED)

        fv = _parse_first_number(freq)
        av = _parse_first_number(ampl)
        ov = _parse_first_number(offs)
        pv = _parse_first_number(phas)
        if fv is not None:
            edev.publish(f'c{ch:02d}Frequency', fv, ifChanged=IF_CHANGED)
        if av is not None:
            edev.publish(f'c{ch:02d}Amplitude', av, ifChanged=IF_CHANGED)
        if ov is not None:
            edev.publish(f'c{ch:02d}Offset', ov, ifChanged=IF_CHANGED)
        if pv is not None:
            edev.publish(f'c{ch:02d}Phase', pv, ifChanged=IF_CHANGED)

    except VisaIOError:
        handle_exception(f'in read_channel_settings(C{ch})')


def refresh_all_settings():
    """Refresh all key settings from the generator."""
    for ch in range(1, pargs.channels + 1):
        read_channel_settings(ch)
    edev.publish('dateTime', time.strftime('%Y-%m-%d %H:%M:%S'), ifChanged=IF_CHANGED)


def init_visa():
    """Initialize VISA and identify the instrument."""
    resource = pargs.resource
    edev.printi(f'Opening VISA resource {resource}')
    try:
        rm = visa.ResourceManager('@py')
        C_.gen = rm.open_resource(resource)
        C_.gen.timeout = 3000
        C_.gen.read_termination = '\n'
        C_.gen.write_termination = '\n'
        idn = _safe_query('*IDN?')
    except (VisaIOError, ModuleNotFoundError):
        handle_exception(f'opening {resource}')
        sys.exit(1)

    edev.publish('genIDN', idn)
    if 'KEYSIGHT' not in idn.upper() and 'AGILENT' not in idn.upper():
        edev.printw(f'Connected instrument does not identify as Keysight/Agilent: {idn}')
    else:
        edev.printi(f'IDN: {idn}')


def build_scpi_map():
    """Build PV->SCPI map used by setters."""
    C_.pv_scpi = {}
    for pvdef in C_.PvDefs:
        if len(pvdef) > 3 and 'scpi' in pvdef[3]:
            C_.pv_scpi[pvdef[0]] = pvdef[3]['scpi']


def serverStateChanged(newState: str):
    """Called by epicsdev when server state changes."""
    if newState == 'Start':
        edev.printi('Start requested')
        refresh_all_settings()
    elif newState == 'Stop':
        edev.printi('Stop requested')
    elif newState == 'Exit':
        edev.printi('Exit requested')


def poll():
    """Main polling hook (lightweight)."""
    edev.publish('pollCount', edev.pvv('pollCount') + 1)


def periodic_update():
    """Slow periodic update for sync with front-panel changes."""
    refresh_all_settings()


def init():
    """Initialize external connection and internal maps."""
    init_visa()
    build_scpi_map()
    refresh_all_settings()
    edev.publish('VERSION', __version__)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=__version__,
    )
    parser.add_argument('-a', '--autosave', nargs='?', default='', help=
        'Autosave control. If not given, autosave is enabled with default directory.')
    parser.add_argument('-c', '--recall', action='store_false', help=
        'If given: do not restore initial PV values from autosave cache.')
    parser.add_argument('-C', '--channels', type=int, default=DEFAULT_CHANNELS, help=
        'Number of generator channels to expose as PVs.')
    parser.add_argument('-d', '--device', default='keysight33000_', help=
        'Device name, the PV prefix is <device><index>:')
    parser.add_argument('-i', '--index', default='0', help=
        'Device index, the PV prefix is <device><index>:')
    parser.add_argument('-p', '--putlogPV', nargs='?', default='', help=
        'PV name for logging put operations. Empty means default putlog:dump.')
    parser.add_argument('-r', '--resource', default=DEFAULT_VISA_RESOURCE, help=
        'VISA resource string for the signal generator.')
    parser.add_argument('-v', '--verbose', action='count', default=0, help=
        'Increase verbosity (-vv for more).')

    pargs = parser.parse_args()
    if pargs.putlogPV == '':
        pargs.putlogPV = 'putlog:dump'

    pargs.prefix = f'{pargs.device}{pargs.index}:'
    C_.PvDefs = myPVDefs()

    PVs = edev.init_epicsdev(
        pargs.prefix,
        C_.PvDefs,
        pargs.verbose,
        serverStateChanged,
        '',
        pargs.autosave,
        pargs.recall,
        pargs.putlogPV,
    )

    init()
    edev.set_server('Start')

    server = edev.Server(providers=[PVs])
    edev.printi(
        f'Server for {pargs.prefix} started. Sleeping per cycle: {repr(edev.pvv("sleep"))} S.'
    )
    while True:
        state = edev.serverState()
        if state.startswith('Exit'):
            break
        if not state.startswith('Stop'):
            poll()
        if not edev.sleep():
            periodic_update()

    edev.printi('Server is exited')
