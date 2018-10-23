# GoPro API for Python using asyncio and aiohttp
Started of as a fork of https://github.com/KonradIT/gopro-py-api and
who knows, it might be merged back in there.

__Warning__ This is very much a work in progress.

[![GitHub issues](https://img.shields.io/github/issues/kmpm/py-asyncio-goproapi.svg)]

Unofficial GoPro API Library for Python - connect to GoPro cameras via WiFi.
![](http://i.imgur.com/kA0Rf1b.png)

# Major changes from gopro-py-api
* asyncio and aiohttp instead of urllib
* no prints
* flake8
* will be dropping HERO3, HERO3+ support


# Compatibility:
| Camera                          | gopro-py-api | this library        |
| ------------------------------- | ------------ | ------------------- |
| HERO3                           | Yes          | No                  |
| HERO3+                          | Yes          | No                  |
| HERO4 (including HERO Session)  | Yes          | Yes                 |
| HERO+                           | Yes          | not tested          |
| HERO5 (including HERO5 Session) | Yes          | not tested          |
| HERO6                           | Yes          | not tested          |
| Fusion 1                        | Yes          | not tested          |
| HERO7 (Black)                   | Yes          | not tested          |


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
