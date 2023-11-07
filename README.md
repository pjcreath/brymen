Brymen BM257s Serial Library
============================

Small Python 3 library to access the serial interface of Brymen BM257s multimeters. It is developed with the Brymen BRUA-20X USB kit and uses the Brymen 6000-count digital multimeter communication protocol, so it should work with other BM25x models as well.

The library reads the serial stream sent by the meter in a dedicated thread, so that you can query the current value at any time without any special effort on your part.

Installation
------------

The easiest way to install this library is to use pip within a virtualenv:

```console
$ git clone git@github.com:RobertWilbrandt/bm257s.git && cd bm257s  # Clone library
$ pip3 install -r requirements.txt  # Install requirements
$ pip3 install .  # Install library
```

Basic Usage
-----------
**Example 1**: For a very quick test of connectivity, you can bring up a text console showing the current reading from the meter:

```console
./scripts/bm257s-console /dev/USBPORT
```

If you're not getting any data, remember to hold down the `HOLD` button on the meter while turning it on.

**Example 2**: To print a line every time the meter transmits an update (roughtly every 200 ms):

```python
with BM257sSerialInterface(port) as interface:  # open the port and start the reader thread
	while True:
		interface.wait()  # block until there's data
		measurement = interface.read()
		print(str(measurement))
```

**Example 3**: To print the 2-second average reading and standard deviation at 10-second intervals:

```python
interface = BM257sSerialInterface(port, window=2)  # open the port
interface.start()  # start the reader thread
interface.wait()  # wait for meter to start transmitting
time.sleep(2)
while True:
	measurements = interface.read_all()
	if measurements:
		average = bm257s.measurement.average(measurements)
		stdev = statistics.stdev(average.values)
		print(f"{str(average)} SD={stdev}")
	time.sleep(10)
```

**Output**

The `read()` function returns a Measurement subclass, representing the most recent measurement, with the following properties:

- `type`: The physical property being measured: "Voltage", "Temperature", etc.
- `unit`: The base units for that property: V, Vrms, Ω, etc.  For temperature, "C" and "F" indicate which scale is being used by the meter.
- `value`: The floating-point value in those units
- `display_unit`: The range of units being measured, as shown on the meter display: mV, kΩ, etc.
- `display_value`: The floating-point value in those units, as shown on the meter display

The `read_all()` function returns a list of `Measurement` objects representing the most recent measurements received from the meter within the configured window.

These measurements can be individually processed or automatically combined using the `measurement.average()` function.  The resulting single Measurement includes an additional `values` property containing the list of all non-null values used to compute the average `value`.

For more detail, use the `help()` function in Python.

Limitations
-----------

The library currently does not support all measuring modes. In the table below, "semi-complete" means that it will give you the correct values if you already have the mode selected on the meter.  "Complete" means it will also detect whether or not you are in the given mode.

| Measuring mode   | Semi-Complete | Complete|
|------------------|:-------------:|---------|
| Temperature (°C) |               | X       |
| Temperature (°F) |               | X       |
| Resistance (Ω)   |               | X       |
| Resistance (kΩ)  |               | X       |
| Resistance (MΩ)  |               | X       |
| Voltage DC (V)   |               | X       |
| Voltage AC (V)   |               | X       |
| Current (uA)     |               |         |
| Current (mA)     |               |         |
| Current (A)      |               |         |
| Capacitance (nF) |               |         |
| Capacitance (uF) |               |         |

Additionally, the library only supports a single Brymen protocol.  See [TODO.md](TODO.md).

Contributing
------------

This project uses various linters to enforce its code style:

- The [black](https://black.readthedocs.io/en/stable/) code formatter
- [isort](https://pycqa.github.io/isort/) for nicely sorted imports
- The [flake8](https://flake8.pycqa.org/en/latest/) linter
- The [pylint](https://www.pylint.org/) linter

They are integrated into automatic testing and run automatically in CI.

Testing
-------

This project uses [tox](https://tox.readthedocs.io/en/latest/) for testing automation. It runs the included [unittest](https://docs.python.org/3/library/unittest.html) tests and checks the linters discussed in [Code Style](#code-style).

If you want to run the tests locally you first need to install ```tox``` using ```pip3 install tox```. Then you should be able to start testing:

```console
$ tox
```
