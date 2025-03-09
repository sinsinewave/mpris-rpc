# MPRIS-RPC
MPRIS2 Music Player Integration for Discord Rich Presence


## Usage
* Install Python dependencies from either PyPI or your distributions repository: `mpris2`, `dbus`, `requests`
* Install the development release of `pypresence` using `pip install https://github.com/qwertyquerty/pypresence/archive/master.zip`
* Create an application on Discord's [developer portal](https://discord.com/developers/applications) according to Discord's documentation
* Place your application's client ID in `main.py`
* Run `main.py`

It is recommended to either tie starting the script to your music player, or to run it as a daemon using your init system of choice.
