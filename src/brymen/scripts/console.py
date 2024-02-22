#!/usr/bin/env python3
"""Minimal console for monitoring brymen bm257s multimeter data"""
# pylint: disable=invalid-name

import argparse
import curses
import datetime
import sys
import time

import bm257s

PORT = "/dev/cu.usbserial-1430"


def curses_main(stdscr, interface):
    """Start minimal bm257s console

    :param stdscr: Curses window object
    :type stdscr: curses.window
    :param interface: Multimeter interface
    :type interface: bm257s.BM257sSerialInterface
    """
    stdscr.clear()
    curses.use_default_colors()

    COLOR_PAIR_STATUS_OK = 1
    curses.init_pair(COLOR_PAIR_STATUS_OK, curses.COLOR_GREEN, -1)
    COLOR_PAIR_STATUS_ERR = 2
    curses.init_pair(COLOR_PAIR_STATUS_ERR, curses.COLOR_RED, -1)

    stdscr.addstr(1, 1, "Quantity:")
    win_qty = curses.newwin(1, 20, 1, 20)
    stdscr.addstr(2, 1, "Measurement:")
    win_meas = curses.newwin(1, 20, 2, 20)

    stdscr.addstr(4, 1, "Status:")
    status = False
    win_status = curses.newwin(1, 30, 4, 10)

    conn_last = datetime.datetime.min
    connected = False
    win_conn = curses.newwin(1, 40, 6, 1)

    while 1:
        try:
            # Read from interface
            if interface.window:
                measurements = interface.read_all(clear=False)
                measurement = bm257s.measurement.average(measurements)
            else:
                measurement = interface.read()
            if measurement is not None:
                win_qty.addstr(0, 0, f"{measurement.type:>19}")
                win_meas.addstr(0, 0, f"{str(measurement):>19}")

            status = connected

        except RuntimeError:
            status = False

        # Update connection status
        now = datetime.datetime.now()
        if (now - conn_last).total_seconds() > 1.0:
            connected = False
            conn_state_str = "Not Connected"
        else:
            connected = True
            conn_state_str = "Connected"
        win_conn.addstr(0, 0, f"{conn_state_str:>39}", curses.A_REVERSE)
        conn_last = now

        # Update status
        if status:
            win_status.addstr(
                0, 0, f"{'OK':>29}", curses.color_pair(COLOR_PAIR_STATUS_OK)
            )
        else:
            win_status.addstr(
                0, 0, f"{'ERROR':>29}", curses.color_pair(COLOR_PAIR_STATUS_ERR)
            )

        # Update windows
        stdscr.refresh()
        win_qty.refresh()
        win_meas.refresh()
        win_status.refresh()
        win_conn.refresh()

        time.sleep(0.1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("port", nargs='?',
                        default="/dev/ttyUSB0",
                        help="serial port to use, defaults to /dev/ttyUSB0"
                        )
    parser.add_argument("--window", default=None, type=float, metavar="SECONDS",
                        help="how long to average samples, defaults to single sample",
                        )
    parser.add_argument("--log", default=None,
                        help="filepath at which to log incoming data"
                        )
    args = parser.parse_args()
    try:
        with bm257s.BM257sSerialInterface(port=args.port, read_timeout=1.0,
                                          window=args.window, log=args.log) as mm:
            try:
                curses.wrapper(curses_main, mm)
            except KeyboardInterrupt:
                curses.endwin()

    except RuntimeError as ex:
        print(f"Could not open serial device: {ex}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
