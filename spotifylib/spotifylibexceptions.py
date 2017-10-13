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
    Generic error handler while interacting with Spotify API

    These errors appear when trying to get access grants and we get a ``400`` Error

    Examples:
    ---------
        - Wrong client_id
        ``'INVALID_CLIENT: Invalid client'``

        - Wrong response_type
        ``'response_type must be code or token'``

        - Invalid scope
        ``'INVALID_SCOPE: Invalid scope'``

        - Invalid CSRF cookie
        ``'{"error":"errorCSRF"}'``

        - Invalid redirect_uri
        ``'Illegal redirect_uri'``
    """
    pass
