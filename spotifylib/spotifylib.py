#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
# File: spotifylib.py
"""
Main module file

Put your classes here
"""

from requests import Session
from requests.exceptions import RequestException
from bs4 import BeautifulSoup as Bfs
from urllib import quote
from base64 import b64encode
from constants import *
from collections import namedtuple
import ast
import logging
from spotipy import Spotify as SpotifyToPatch


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
        self._request_app_authorization()
        self._login_to_account()
        self._get_authorization()
        response = self._accept_app_to_account()
        if not response.ok:
            raise RequestException("Couldn't get code to request token")
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
    def __get_bon(response_page):
        soup = Bfs(response_page, 'html.parser')
        # TODO unsafe index reference. Handle better.
        meta = soup.find_all('meta')[-1]
        data = ast.literal_eval(meta.attrs.get('sp-bootstrap-data'))
        bon = data.get('BON')
        if not bon:
            raise ValueError("Bon not found", "Meta: {meta} \n"
                                              "Data: {data}".format(meta=meta,
                                                                    data=data))
        bon.extend([bon[-1] * 42, 1, 1, 1, 1])
        __bon = b64encode('|'.join([str(entry) for entry in bon]))
        return __bon

    def _request_app_authorization(self):
        params = {'scope': self._scope,
                  'redirect_uri': self._callback,
                  'response_type': 'code',
                  'client_id': self.user.client_id}
        response = self.session.get(AUTH_WEB_URL, params=params)
        if not response.ok:
            raise RequestException("Failed to get authorization page")
        __bon_cookie = {'name': '__bon',
                        'value': self.__get_bon(response.text)}
        self.session.cookies.set(**__bon_cookie)
        return True

    def _login_to_account(self):
        fb_value = ('{auth}?scope={scope}&'.format(auth=AUTH_WEB_URL,
                                                   scope=quote(self._scope,
                                                               safe=':')),
                    'redirect_uri={call}&'.format(call=quote(self._callback,
                                                             safe=':')),
                    'response_type=code&',
                    'client_id={cl_id}'.format(cl_id=self.user.client_id))
        __fb_cookie = {'name': 'fb_continue',
                       'value': ''.join(fb_value)}
        self.session.cookies.set(**__fb_cookie)
        payload = {'remember': 'true',
                   'username': self.user.username,
                   'password': self.user.password,
                   'csrf_token': self.session.cookies.get('csrf_token')}
        response = self.session.post(API_LOGIN_URL,
                                     data=payload,
                                     headers=HEADERS)
        if not response.ok:
            raise RequestException("Failed to login to API")
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
            raise RequestException("Failed to authorize APP")
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
        if not response.ok:
            raise RequestException("Failed to accept APP to account")
        return response

    def _get_token(self, response):
        # TODO unsafe index reference. Handle better.
        try:
            code = response.json().get('redirect', '').split('code=')[1]
        except (AttributeError, IndexError):
            self._logger.exception(response.content)
            raise
        payload = {'grant_type': 'authorization_code',
                   'code': code,
                   'redirect_uri': self._callback}
        base64encoded = b64encode("{}:{}".format(self.user.client_id,
                                                 self.user.client_secret))
        headers = {'Authorization': 'Basic {}'.format(base64encoded)}
        response = self.session.post(TOKEN_URL,
                                     data=payload,
                                     headers=headers)
        if not response.ok:
            raise RequestException("Failed to get token")
        values = [response.json().get(key) for key in Token._fields]
        if not all(values):
            raise RequestException('Incomplete token response received.')
        return Token(*values)

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
        base64encoded = b64encode('{}:{}'.format(user.client_id,
                                                 user.client_secret))
        headers = {'Authorization': 'Basic {}'.format(base64encoded)}
        response = session.post(TOKEN_URL,
                                data=payload,
                                headers=headers)
        if not response.ok:
            raise RequestException("Couldn't get new token from refresh token")

        values = [response.json().get(key) for key in Token._fields]
        if not all(values):
            raise RequestException('Incomplete token response received.')
        return Token(*values)

    def _monkey_patch_session(self):
        self.session._original_get = self.session.get
        self.session.token = self.token
        self.session.user = self.user
        self.session.get = self._patched_get

    def _patched_get(self, *args, **kwargs):
        print('patched_get!###################################################')
        response = self.session._original_get(*args, **kwargs)
        if response.status_code == 401 \
            and response.json().get('message') == 'The access token expired':
            self.session.token = self._renew_token(self.session,
                                                   self.user,
                                                   self.token)
            response = self.session._original_get(*args, **kwargs)
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
        spotify = SpotifyToPatch(auth=authenticated.token,
                                 requests_session=authenticated.session)
        return spotify
