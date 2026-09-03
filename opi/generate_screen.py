"""Generate a simple Phoebus screen for Keysight 33000 PVs."""
__version__ = 'v0.0.2 2026-08-26'

import argparse
from pathlib import Path

import phoebusgen.screen
import phoebusgen.widget

DEFAULT_PREFIX = "$(DEV):"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=__version__,
    )
    parser.add_argument("-t", "--title", default="Keysight 33000", help="Screen title")
    parser.add_argument(
        "prefix",
        nargs="?",
        default=DEFAULT_PREFIX,
        help=(
            "PV prefix used for all widget PV names. "
            "If not specified, the prefix is `$(DEV):`, it can be defined in screen macros."
        ),
    )
    return parser.parse_args()


def main() -> None:
    pargs = _parse_args()
    prefix = pargs.prefix

    screen = phoebusgen.screen.Screen(pargs.title, "keysight_33000.bob")
    screen.width(980)
    screen.height(420)

    w = phoebusgen.widget
    widgets = {
        "title": w.Label("title", "Keysight 33000", 20, 10, 220, 30),
        "genIDN": w.TextUpdate("genIDN", f"{prefix}genIDN", 210, 10, 520, 20),
        "dateTime": w.TextUpdate("dateTime", f"{prefix}dateTime", 740, 10, 210, 20),

        "state_lbl": w.Label("state_lbl", "Run/Stop:", 20, 42, 70, 20),
        "server": w.ComboBox("server", f"{prefix}server", 95, 42, 110, 20),
        "sleep_lbl": w.Label("sleep_lbl", "Sleep [s]:", 220, 42, 65, 20),
        "sleep": w.TextEntry("sleep", f"{prefix}sleep", 290, 42, 80, 20),
        "poll_lbl": w.Label("poll_lbl", "Poll Count:", 390, 42, 70, 20),
        "pollCount": w.TextUpdate("pollCount", f"{prefix}pollCount", 470, 42, 110, 20),

        "ch1_lbl": w.Label("ch1_lbl", "Channel 1", 20, 80, 90, 20),
        "c01Output_lbl": w.Label("c01Output_lbl", "Output:", 20, 105, 55, 20),
        "c01Output": w.ComboBox("c01Output", f"{prefix}c01Output", 80, 105, 80, 20),
        "c01Load_lbl": w.Label("c01Load_lbl", "Load:", 175, 105, 40, 20),
        "c01Load": w.ComboBox("c01Load", f"{prefix}c01Load", 220, 105, 70, 20),
        "c01Polarity_lbl": w.Label("c01Polarity_lbl", "Polarity:", 305, 105, 55, 20),
        "c01Polarity": w.ComboBox("c01Polarity", f"{prefix}c01Polarity", 365, 105, 100, 20),
        "c01WaveType_lbl": w.Label("c01WaveType_lbl", "Wave:", 475, 105, 45, 20),
        "c01WaveType": w.ComboBox("c01WaveType", f"{prefix}c01WaveType", 525, 105, 80, 20),
        "c01Frequency_lbl": w.Label("c01Frequency_lbl", "Freq [Hz]:", 620, 105, 60, 20),
        "c01Frequency": w.TextEntry("c01Frequency", f"{prefix}c01Frequency", 685, 105, 110, 20),
        "c01Amplitude_lbl": w.Label("c01Amplitude_lbl", "Amp [Vpp]:", 810, 105, 65, 20),
        "c01Amplitude": w.TextEntry("c01Amplitude", f"{prefix}c01Amplitude", 880, 105, 80, 20),
        "c01Offset_lbl": w.Label("c01Offset_lbl", "Offset [V]:", 620, 130, 60, 20),
        "c01Offset": w.TextEntry("c01Offset", f"{prefix}c01Offset", 685, 130, 110, 20),
        "c01Phase_lbl": w.Label("c01Phase_lbl", "Phase [deg]:", 810, 130, 65, 20),
        "c01Phase": w.TextEntry("c01Phase", f"{prefix}c01Phase", 880, 130, 80, 20),

        "scpi_lbl": w.Label("scpi_lbl", "SCPI:", 20, 155, 40, 20),
        "instrCmdS": w.TextEntry("instrCmdS", f"{prefix}instrCmdS", 65, 155, 250, 20),
        "reply_lbl": w.Label("reply_lbl", "Reply:", 330, 155, 40, 20),
        "instrCmdR": w.TextUpdate("instrCmdR", f"{prefix}instrCmdR", 375, 155, 585, 20),
    }

    for item in "Start, Stop, Clear, Exit, Started, Stopped, Exited".split(", "):
        widgets["server"].item(item)

    ch = "c01"
    for item in "OFF, ON".split(", "):
        widgets[f"{ch}Output"].item(item)
    for item in "50, INF".split(", "):
        widgets[f"{ch}Load"].item(item)
    for item in "NORMal, INVerted".split(", "):
        widgets[f"{ch}Polarity"].item(item)
    for item in "SIN, SQU, RAMP, PULS, NOIS, DC, ARB".split(", "):
        widgets[f"{ch}WaveType"].item(item)

    widgets["sleep"].precision(2)
    widgets["pollCount"].format("Decimal")
    widgets["pollCount"].precision(0)

    name = "c01Frequency"
    widgets[name].format("Exponential")
    widgets[name].precision(3)

    widgets["instrCmdR"].wrap_words(False)

    screen.add_widget(list(widgets.values()))

    out = Path(__file__).with_name("keysight_33000.bob")
    screen.write_screen(str(out))


if __name__ == "__main__":
    main()
