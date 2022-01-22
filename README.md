## What is Winelyze?

Winelyze is an experiment to determine how well using WINE in an unpriviliged Docker container can be in malware analysis. Although it may not a complete analysis, Docker images with WINE are alot more scalable than large numbers of Windows VMs, and may be useful as a first-pass analysis.

> This project is currently in an experiment phase, don't expect things to be done or fully implemented.

## Setup

Configure Docker for be unprivileged:

` /etc/docker/daemon.json`:
```
{
    "userns-remap": "default"
}
```

Create venv:
```
python3 -m venv ./venv
source ./venv/bin/activate
pip3 install -r requirements.txt
```

Build Docker images in `inetsim` (network stuff) and `winelyze`. The `python3 build.py` should work or `docker build . -t <DIR>`

## Test Sample
In the `winelyze` dir, run:
```
python3 run.py --file ../pafish64.exe
```