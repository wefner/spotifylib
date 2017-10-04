#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
# File: spotifylib.py
"""
Main module file

Put your classes here
"""

import inspect
from requests import Session
from urllib import quote
from base64 import b64encode
from constants import *
from collections import namedtuple
from spotipy import Spotify as OriginalSpotify
from spotifylibexceptions import SpotifyError

import logging


__author__ = '''Oriol Fabregas <fabregas.oriol@gmail.com>'''
__docformat__ = 'plaintext'
__date__ = '''18-09-2017'''

# This is the main prefix used for logging
LOGGER_BASENAME = '''spotifylib'''
LOGGER = logging.getLogger(LOGGER_BASENAME)
LOGGER.addHandler(logging.NullHandler())


Token = namedtuple('Token', ['access_token',
                             'token_type',
                             'expires_in',
                             'refresh_token',
                             'scope'])

User = namedtuple('User', ['client_id',
                           'client_secret',
                           'username',
                           'password'])


class SpotifyAuthenticator(object):
    def __init__(self,
                 client_id,
                 client_secret,
                 username,
                 password,
                 callback,
                 scope):
        self._logger = logging.getLogger('{base}.{suffix}'
                                         .format(base=LOGGER_BASENAME,
                                                 suffix=self.__class__.__name__)
                                         )
        self.user = User(client_id, client_secret, username, password)
        self._callback = callback
        self._scope = scope
        self._token = None
        self.session = Session()
        HEADERS.update({'Referer': self._get_referer()})
        self.__authenticate()

    @property
    def token(self):
        return self._token

    def __authenticate(self):
        self._get_authorization()
        self._login_to_account()
        response = self._accept_app_to_account()
        self._token = self._get_token(response)
        self._monkey_patch_session()
        return True

    def _get_referer(self):
        params = ('{auth}?scope={scope}&'.format(auth=AUTH_WEB_URL,
                                                 scope=quote(self._scope)),
                  'redirect_uri={call}?'.format(call=quote(self._callback,
                                                           safe=':')),
                  'response_type=code?',
                  'client_id={client_id}'.format(client_id=self.user.client_id))
        referer = ('{login_url}?'.format(login_url=LOGIN_WEB_URL),
                   'continue={params}'.format(params=quote(''.join(params),
                                                           safe=':')))
        return ''.join(referer)

    @staticmethod
    def __get_bon(response):
        try:
            bon = response.json().get('BON', [])
        except ValueError:
            raise SpotifyError("Response page couldn't be decoded")
        if not bon:
            raise ValueError("Bon not found. Got {}".format(response.content))
        bon.extend([bon[-1] * 42, 1, 1, 1, 1])
        __bon = b64encode('|'.join([str(entry) for entry in bon]))
        return __bon

    def _login_to_account(self):
        payload = {'remember': 'true',
                   'username': self.user.username,
                   'password': self.user.password,
                   'csrf_token': self.session.cookies.get('csrf_token')}
        response = self.session.post(API_LOGIN_URL,
                                     data=payload,
                                     headers=HEADERS)
        if response.status_code == 400:
            self._logger.exception(response.content)
            raise SpotifyError("Failed to login to API. "
                               "Message: {}".format(response.content))
        return True

    def _get_authorization(self):
        params = {'scope': self._scope,
                  'redirect_uri': self._callback,
                  'response_type': 'code',
                  'client_id': self.user.client_id}
        response = self.session.get(AUTH_WEB_URL,
                                    headers=HEADERS,
                                    params=params)
        if not response.ok:
            self._logger.exception(response.content)
            raise SpotifyError("Failed to get authorization page. "
                               "Message: {}".format(response.content))
        __bon_cookie = {'name': '__bon',
                        'value': self.__get_bon(response)}
        self.session.cookies.set(**__bon_cookie)
        return True

    def _accept_app_to_account(self):
        payload = {'scope': self._scope,
                   'redirect_uri': self._callback,
                   'response_type': 'code',
                   'client_id': self.user.client_id,
                   'csrf_token': self.session.cookies.get('csrf_token')}
        response = self.session.post(ACCEPT_URL,
                                     data=payload,
                                     headers=HEADERS)
        if response.status_code == 400:
            self._logger.exception(response.content)
            raise SpotifyError(response.content)
        return response

    def _get_token(self, response):
        try:
            code = response.json().get('redirect', '').split('code=')[1]
        except (AttributeError, IndexError):
            self._logger.exception(response.content)
            raise SpotifyError("Error while getting the token. "
                               "Got: {}".format(response.content))
        payload = {'grant_type': 'authorization_code',
                   'code': code,
                   'redirect_uri': self._callback}
        return self._retrieve_token(self.session, self.user, payload)

    @staticmethod
    def _renew_token(session, user, token):
        """
        >>> response.json()
        {u'error': {u'status': 401, u'message': u'The access token expired'}}

        :param refresh_token:
        :return:
        """
        payload = {'grant_type': 'refresh_token',
                   'refresh_token': token.refresh_token}
        return SpotifyAuthenticator._retrieve_token(session, user, payload)

    @staticmethod
    def _retrieve_token(session, user, payload):
        base64encoded = b64encode('{}:{}'.format(user.client_id,
                                                 user.client_secret))
        headers = {'Authorization': 'Basic {}'.format(base64encoded)}
        response = session.post(TOKEN_URL,
                                data=payload,
                                headers=headers)
        if response.status_code == 400:
            LOGGER.exception(response.content)
            raise SpotifyError("Couldn't get new token from refresh token. "
                               "Got: {}".format(response.content))

        values = [response.json().get(key) for key in Token._fields]
        if not values[3]:
            # in case of refresh, we don't get the refresh token back so we will
            # just inject it. Of course we should already have it since this is
            # a refresh request so session should already be set up maybe this
            # can be a little simpler, hm....
            values[3] = session.token.refresh_token
        if not all(values):
            LOGGER.exception(response.content)
            raise ValueError('Incomplete token response received. '
                             'Got: {}'.format(response.json()))
        return Token(*values)

    def _monkey_patch_session(self):
        self.session.original_request = self.session.request
        self.session.token = self.token
        self.session.user = self.user
        self.session.renew_token = self._renew_token
        self.session.request = self._patched_request

    def _patched_request(self, method, url, **kwargs):
        self._logger.debug(('Using patched request for method {method}, '
                            'url {url}').format(method=method, url=url))
        response = self.session.original_request(method, url, **kwargs)
        # TODO move the expired token json into constants.py and check for
        # equality so it is easier to update.
        # Something like:
        # if response.status_code == 401 and response.json() == EXPIREDTOKENJSON
        if response.status_code == 401 \
            and response.json().get('error', {}
                                    ).get('message'
                                          ) == 'The access token expired':
            self._logger.warning('Expired token detected, trying to refresh!')
            self.session.token = self.session.renew_token(self.session,
                                                          self.user,
                                                          self.token)
            token = self.session.token.access_token
            self.session.parent._auth = token
            kwargs['headers'].update({'Authorization': 'Bearer {}'.format(token)
                                      })
            self._logger.debug('Updated headers, trying again initial request')
            response = self.session.original_request(method, url, **kwargs)
        return response


class Spotify(object):
    def __new__(cls,
                client_id,
                client_secret,
                username,
                password,
                callback,
                scope):
        authenticated = SpotifyAuthenticator(client_id,
                                             client_secret,
                                             username,
                                             password,
                                             callback,
                                             scope)
        spotify = OriginalSpotify(auth=authenticated.token.access_token,
                                  requests_session=authenticated.session)
        spotify._session.parent = spotify
        return spotify
