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


class Spotify(object):
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
        self._client_id = client_id
        self._client_secret = client_secret
        self._username = username
        self._password = password
        self._callback = callback
        self._scope = scope
        self._token = None
        self.session = Session()
        HEADERS.update({'Referer': self._get_referer()})
        self.__authenticate()

    def __authenticate(self):
        self._request_app_authorization()
        self._login_to_account()
        self._get_authorization()
        response = self._accept_app_to_account()
        if not response.ok:
            raise RequestException("Couldn't get code to request token")
        self._token = self._get_token(response)
        return True

    def _get_referer(self):
        params = ('{auth}?scope={scope}&'.format(auth=AUTH_WEB_URL,
                                                 scope=quote(self._scope)),
                  'redirect_uri={call}?'.format(call=quote(self._callback,
                                                           safe=':')),
                  'response_type=code?',
                  'client_id={client_id}'.format(client_id=self._client_id))
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
                  'client_id': self._client_id}
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
                    'client_id={client_id}'.format(client_id=self._client_id))
        __fb_cookie = {'name': 'fb_continue',
                       'value': ''.join(fb_value)}
        self.session.cookies.set(**__fb_cookie)
        payload = {'remember': 'true',
                   'username': self._username,
                   'password': self._password,
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
                  'client_id': self._client_id}
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
                   'client_id': self._client_id,
                   'csrf_token': self.session.cookies.get('csrf_token')}
        response = self.session.post(ACCEPT_URL,
                                     data=payload,
                                     headers=HEADERS)
        if not response.ok:
            raise RequestException("Failed to accept APP to account")
        return response

    def _get_token(self, response):
        token_keys = ['access_token',
                      'token_type',
                      'expires_in',
                      'refresh_token',
                      'scope']
        # TODO unsafe index reference. Handle better.
        code = response.json().get('redirect').split('code=')[1]
        payload = {'grant_type' : 'authorization_code',
                   'code': code,
                   'redirect_uri': self._callback}
        base64encoded = b64encode("{}:{}".format(self._client_id,
                                                 self._client_secret))
        headers = {'Authorization': 'Basic {}'.format(base64encoded)}
        response = self.session.post(TOKEN_URL,
                                     data=payload,
                                     headers=headers)
        if not response.ok:
            raise RequestException("Failed to get token")
        values = [response.json().get(key) for key in token_keys]
        if not all(values):
            raise RequestException('Incomplete token response received.')
        return Token(*values)
