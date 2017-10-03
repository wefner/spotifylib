# -*- coding: utf-8 -*-
"""
spotifylib package

Imports all parts from spotifylib here
"""
from ._version import __version__
from .constants import *
from spotifylib import Spotify
from spotifylibexceptions import SpotifyError

__author__ = '''Oriol Fabregas'''
__email__ = '''fabregas.oriol@gmail.com'''

# This is to 'use' the module(s), so lint doesn't complain
assert __version__


# assert objects
assert Spotify
assert SpotifyError
