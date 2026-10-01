"""Generate a Phoebus operator interface for a Keysight 33000 generator."""
__version__ = 'v0.0.1 2026-10-01'
# pylint: disable=invalid-name,broad-exception-caught

import argparse
from pathlib import Path

import phoebusgen.screen
import phoebusgen.widget

DEVICE = "keysight33000"
INSTANCE = "0"
TITLE = "Keysight 33000"
PREFIX = f'pva://{DEVICE}:{INSTANCE}:'

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=__version__,
    )
    parser.add_argument("-t", "--title", default=TITLE, help="Screen title")
    parser.add_argument("prefix", nargs="?", default=PREFIX,
        help=(
            "PV prefix used for all widget PV names. "
        ),
    )
    return parser.parse_args()

def _add_items(widget, values: str) -> None:
    for item in values.split(", "):
        widget.item(item)

def main() -> None:
    pargs = _parse_args()
    prefix = pargs.prefix

    screen = phoebusgen.screen.Screen(pargs.title, f"{DEVICE}.bob")
    screen.width(1080)
    screen.height(300)

    w = phoebusgen.widget
    widgets = {
        "title": w.Label("title", TITLE, 20, 10, 180, 30),
        "genIDN": w.TextUpdate("genIDN", f"{prefix}genIDN", 210, 14, 470, 20),
        "dateTime": w.TextUpdate("dateTime", f"{prefix}dateTime", 700, 14, 180, 20),
        "resource_lbl": w.Label("resource_lbl", "VISA:", 890, 14, 40, 20),
        "visaResource": w.TextUpdate("visaResource", f"{prefix}visaResource", 935, 14, 130, 20),
    }
    y = 50
    widgets.update({
        "srvStatus_lbl": w.Label("srvStatus_lbl", "Server:", 20, y, 100, 20),
        "srvStatus": w.TextUpdate("srvStatus", f"{prefix}status", 70, y, 790, 20),
    })
    y += 35
    widgets.update({
        "state_lbl": w.Label("state_lbl", "Run/Stop:", 20, y, 65, 20),
        "server": w.ComboBox("server", f"{prefix}server", 90, y, 110, 20),
        "sleep_lbl": w.Label("sleep_lbl", "Sleep:", 410, y, 40, 20),
        "sleep": w.TextEntry("sleep", f"{prefix}sleep", 450, y, 50, 20),
        "cycleTime_lbl": w.Label("cycleTime_lbl", "Period:", 510, y, 50, 20),
        "cycleTime": w.TextUpdate("cycleTime", f"{prefix}cycleTime", 560, y, 60, 20),
        "hb_lbl": w.Label("hb_lbl", "HB:", 640, y, 30, 20),
        "HEARTBEAT": w.TextUpdate("HEARTBEAT", f"{prefix}HEARTBEAT", 670, y, 70, 20),
})
    y += 40
    widgets.update({
        "channel_lbl": w.Label("channel_lbl", "Channel 1", 20, y, 90, 20),
        "c01Output_lbl": w.Label("c01Output_lbl", "Output:", 20, y + 25, 50, 20),
        "c01Output": w.ComboBox("c01Output", f"{prefix}c01Output", 75, y + 25, 75, 20),
        "c01Load_lbl": w.Label("c01Load_lbl", "Load:", 165, y + 25, 40, 20),
        "c01Load": w.ComboBox("c01Load", f"{prefix}c01Load", 210, y + 25, 70, 20),
        "c01Polarity_lbl": w.Label("c01Polarity_lbl", "Polarity:", 295, y + 25, 55, 20),
        "c01Polarity": w.ComboBox("c01Polarity", f"{prefix}c01Polarity", 355, y + 25, 85, 20),
        "c01WaveType_lbl": w.Label("c01WaveType_lbl", "Wave:", 455, y + 25, 40, 20),
        "c01WaveType": w.ComboBox("c01WaveType", f"{prefix}c01WaveType", 500, y + 25, 85, 20),
        "c01Frequency_lbl": w.Label("c01Frequency_lbl", "Freq [Hz]:", 600, y + 25, 60, 20),
        "c01Frequency": w.TextEntry("c01Frequency", f"{prefix}c01Frequency", 665, y + 25, 105, 20),
        "c01Amplitude_lbl": w.Label("c01Amplitude_lbl", "Amp [Vpp]:", 785, y + 25, 65, 20),
        "c01Amplitude": w.TextEntry("c01Amplitude", f"{prefix}c01Amplitude", 855, y + 25, 90, 20),
        "c01Offset_lbl": w.Label("c01Offset_lbl", "Offset [V]:", 600, y + 50, 60, 20),
        "c01Offset": w.TextEntry("c01Offset", f"{prefix}c01Offset", 665, y + 50, 105, 20),
        "scpi_lbl": w.Label("scpi_lbl", "SCPI:", 20, y + 90, 40, 20),
        "instrCmdS": w.TextEntry("instrCmdS", f"{prefix}instrCmdS", 65, y + 90, 260, 20),
        "reply_lbl": w.Label("reply_lbl", "Reply:", 340, y + 90, 40, 20),
        "instrCmdR": w.TextUpdate("instrCmdR", f"{prefix}instrCmdR", 385, y + 90, 680, 20),
    })

    for item in "Start, Stop, Clear, Exit, Started, Stopped, Exited".split(", "):
        widgets["server"].item(item)
    for name, values in {
        "c01Output": "OFF, ON",
        "c01Load": "50, INF",
        "c01Polarity": "NORMal, INVerted",
        "c01WaveType": "SIN, SQU, RAMP, PULS, NOIS, DC, USER",
    }.items():
        _add_items(widgets[name], values)

    widgets["sleep"].precision(2)
    #widgets["cycleTime"].format("Decimal")
    widgets["cycleTime"].precision(3)
    widgets["c01Frequency"].format("Exponential")
    widgets["c01Frequency"].precision(3)
    for name in ("c01Amplitude", "c01Offset"):
        widgets[name].format("Engineering")
        widgets[name].precision(3)
    widgets["instrCmdR"].wrap_words(False)

    screen.add_widget(list(widgets.values()))

    out = Path(__file__).with_name(f"{DEVICE}.bob")
    screen.write_screen(str(out))

if __name__ == "__main__":
    main()
