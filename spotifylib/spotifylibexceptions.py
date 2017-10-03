#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
# File: spotifylibexceptions.py
#
"""
Main module Exceptions file

Put your exception classes here
"""

__author__ = '''Oriol Fabregas <fabregas.oriol@gmail.com>'''
__docformat__ = 'plaintext'
__date__ = '''18-09-2017'''


class SpotifyError(Exception):
    """
    # Wrong client_id
    (<Response [400]>, 'INVALID_CLIENT: Invalid client')

    # Wrong response_type
    (<Response [400]>, 'response_type must be code or token')

    # Invalid scope
    (<Response [400]>, 'INVALID_SCOPE: Invalid scope')

    # Invalid CSRF cookie
    (<Response [400]>, '{"error":"errorCSRF"}')

    # Invalid redirect_uri
    (<Response [400]>, 'Illegal redirect_uri')
    "Error while accepting APP to Spotify API"
    """
    pass
