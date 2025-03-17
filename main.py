#! /bin/env python3

from log import log

import typing
import subprocess
import mpris2
import requests
import dbus

from urllib     import parse as parse_url
from time       import sleep
from time       import time
from pypresence import Presence
from pypresence import ActivityType
from pypresence import exceptions as presence_exceptions
# TODO: Switch from pypresence to self-implemented presence system

# Discord application client ID
CLIENT_ID = "YOUR ID HERE"
# Refresh rate of script, can be used to reduce performance hit
RATELIMIT = 2.5

# API URLs and query strings
MUSICBRAINZ_URL   = "https://musicbrainz.org/ws/2/release/?fmt=json&query="
COVERARCHIVE_URL  = "https://coverartarchive.org/release/"
MUSICBRAINZ_QUERY = "artist:\"{}\" AND release:\"{}\""

PLAYER_WHITELIST = ["elisa"]

musicbrainz_headers = {
    "User-Agent" : "MPRIS-RPC/0.0.1 (https://github.com/sinsinewave/mpris-rpc) (Sigma1@tuta.io)"
}

log.info("Starting MPRIS-RPC")


class SongInfo(object):
    def __init__(self, artist, album, title, cover_url=None):
        self.artist    = artist
        self.album     = album
        self.title     = title

        if cover_url:
            self.cover_url = cover_url
        else:
            log.info(f"Fetching cover art for \033[3m{artist} – {album}\033[0m")
            query = parse_url.quote(MUSICBRAINZ_QUERY.format(artist, album))

            idx = 0
            while True:
                # If we run out of releases, give up
                try:
                    release_id = requests.get(MUSICBRAINZ_URL+query, headers=musicbrainz_headers).json()["releases"][idx]['id']
                except IndexError:
                    log.info(f"No cover found for \033[3m{self.artist} – {self.album}\033[0m")
                    self.cover_url = None
                    break
                except KeyError:
                    log.fail("MusicBrainz API returned error")

                cover_data = requests.get(COVERARCHIVE_URL+release_id)

                # If release has no covers, try the next one
                if cover_data.status_code == 404:
                    log.dbug("Cover not found, trying next release")
                    idx += 1
                    continue

                log.info("Found cover")
                cover_json = cover_data.json()
                self.cover_url = cover_json["images"][0]["image"]
                break



def initRPC() -> Presence:
    log.dbug("Starting RPC")
    RPC = Presence(CLIENT_ID)
    # Discord may take a moment to start the RPC server, handle that
    sleep(3)
    try:
        RPC.connect()
        pass
    except (ConnectionRefusedError, presence_exceptions.DiscordNotFound):
        return None

    return RPC


def initMPRIS() -> mpris2.Player:
    log.dbug("Starting MPRIS2")
    try:
        players = mpris2.get_players_uri()
        while True:
            player_uri = next(players)
            log.dbug(f"Found player '{player_uri.split('.')[3]}'")
            if player_uri.split('.')[3] in PLAYER_WHITELIST:
                player = mpris2.Player(dbus_interface_info={"dbus_uri" : player_uri})
                return player
    except StopIteration:
        return None


# Main loop
current_track = None
last_refresh  = time()-15
player        = None
presence      = None
while True:
    try:
        # Check MPRIS and Discord connections first
        if player == None:
            player = initMPRIS()

        if presence == None and player != None:
            presence = initRPC()
        
        # Proceed to fetch song info
        if presence != None and player != None:
            # Clear presence if paused
            if player.PlaybackStatus != player.PlaybackStatus.PLAYING:
                presence.clear()
            else:
                # Get current song info
                title  = player.Metadata["xesam:title"]
                album  = player.Metadata["xesam:album"]
                artist = player.Metadata["xesam:artist"][0]

                if current_track == None \
                or current_track.title  != title \
                or current_track.album  != album \
                or current_track.artist != artist:
                    # Track has changed, update

                    new_cover = None
                    # If album and artist remains same, assume we're in the same album and reuse cover
                    if current_track != None and current_track.album == album and current_track.artist == artist:
                        log.info("Using cached cover")
                        new_cover = current_track.cover_url

                    current_track = SongInfo(artist, album, title, cover_url=new_cover)

                time_start_ms = int(time()*1000 - player.Position/1000)
                time_end_ms   = int(time_start_ms+(player.Metadata["mpris:length"]/1000))

                # Limit discord update interval to 15 seconds, Discord ratelimits to that anyways
                if time() - last_refresh > 15:
                    presence.update(
                        activity_type = ActivityType.LISTENING,
                        details       = current_track.title,
                        state         = current_track.artist,
                        large_text    = current_track.album,
                        large_image   = current_track.cover_url,

                        start = time_start_ms // 1000,
                        end   = time_end_ms   // 1000
                    )
                    last_refresh = time()

    except dbus.exceptions.DBusException:
        log.info("Lost connection to music player")
        presence.clear()
        player = None

    except (presence_exceptions.PipeClosed, presence_exceptions.DiscordError):
        log.info("Lost connection to Discord")
        presence = None
        
    sleep(RATELIMIT)
