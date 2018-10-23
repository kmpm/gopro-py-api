# GoPro API for Python using asyncio and aiohttp
Started of as a fork of https://github.com/KonradIT/gopro-py-api and
who knows, it might be merged in.

__Warning__ This is very much a work in progress.

[![GitHub issues](https://img.shields.io/github/issues/kmpm/py-asyncio-goproapi.svg)]

Unofficial GoPro API Library for Python - connect to GoPro cameras via WiFi.
![](http://i.imgur.com/kA0Rf1b.png)


# Compatibility:

- HERO3
- HERO3+
- HERO4 (including HERO Session)
- HERO+
- HERO5 (including HERO5 Session)
- HERO6 
- Fusion 1
- HERO7 (Black)

# Installation

Git (unstable):

```bash
git clone http://github.com/kmpm/py-asyncio-goproapi
cd py-asyncio-goproapi
python setup.py install
```

Tested on Python 3.5.4 -- **should** work on Linux and Windows and Mac


# Testing
Testing is simplest done using tox
```bash
git clone http://github.com/kmpm/py-asyncio-goproapi
cd py-asyncio-goproapi

#optional virtualenv
python3 -m venv venv
source venv/bin/activate

#install tox
pip install tox

tox
```
