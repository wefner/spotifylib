#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
# File: spotifylib.py
"""
Main module file

Put your classes here
"""

from requests import Session
from bs4 import BeautifulSoup as Bfs
from urllib import quote
from base64 import b64encode
from constants import *
import ast
import logging


__author__ = '''Oriol Fabregas <fabregas.oriol@gmail.com>'''
__docformat__ = 'plaintext'
__date__ = '''18-09-2017'''

# This is the main prefix used for logging
LOGGER_BASENAME = '''spotifylib'''
LOGGER = logging.getLogger(LOGGER_BASENAME)
LOGGER.addHandler(logging.NullHandler())


class Spotify(object):
    def __init__(self,
                 client_id,
                 client_secret,
                 username,
                 password,
                 callback,
                 scope):
        self.__client_id = client_id
        self.__client_secret = client_secret
        self.__username = username
        self.__password = password
        self.__callback = callback
        self.__scope = scope
        self.token = None
        self.session = Session()
        self.__referer = '{AUTH_URL}?scope={SCOPE}&' \
                         'redirect_uri={CALLBACK}?' \
                         'response_type=code?' \
                         'client_id={CLIENT_ID}'.format(
                                                AUTH_URL=AUTHORIZE_WEB_URL,
                                                SCOPE=quote(self.__scope),
                                                CALLBACK=quote(self.__callback,
                                                               safe=':'),
                                                CLIENT_ID=self.__client_id)
        HEADERS.update({
            'Referer': '{LOGIN_URL}?'
                        'continue={REFERER_PARAMS}'.format(LOGIN_URL=LOGIN_WEB_URL,
                                                           REFERER_PARAMS=quote(self.__referer,
                                                                                safe=':'))})
        self.__request_app_authorization()
        self.connect_app_to_spotify_account()

    def __request_app_authorization(self):
        result = False
        params = {'scope': self.__scope,
                  'redirect_uri': self.__callback,
                  'response_type': 'code',
                  'client_id': self.__client_id}
        response = self.session.get(AUTHORIZE_WEB_URL, params=params)
        bon = self.__get_bon(response.text)
        bon_cookie = self.__calculate_bon(bon)
        if self.__validate_bon(bon[2], bon_cookie):
            __bon_cookie = {'name': '__bon',
                            'value': bon_cookie}
            self.session.cookies.set(**__bon_cookie)
            result = True
        return result

    def connect_app_to_spotify_account(self):
        __fb_cookie = {'name': 'fb_continue',
                       'value': '{AUTH_URL}?scope={SCOPE}&'
                                'redirect_uri={CALLBACK}&'
                                'response_type=code&'
                                'client_id={CLIENT_ID}'.format(AUTH_URL=AUTHORIZE_WEB_URL,
                                                               SCOPE=quote(self.__scope, safe=':'),
                                                               CALLBACK=quote(self.__callback, safe=':'),
                                                               CLIENT_ID=self.__client_id)}
        self.session.cookies.set(**__fb_cookie)
        payload = {'remember': 'true',
                   'username': self.__username,
                   'password': self.__password,
                   'csrf_token': self.session.cookies.get('csrf_token')}
        response = self.session.post(API_LOGIN_URL,
                                     data=payload,
                                     headers=HEADERS)
        if response.ok:
            return self.get_authorization()

    def get_authorization(self):
        params = {'scope': self.__scope,
                  'redirect_uri': self.__callback,
                  'response_type': 'code',
                  'client_id': self.__client_id}
        response = self.session.get(AUTHORIZE_WEB_URL,
                                    headers=HEADERS,
                                    params=params)
        if response.ok:
            return self.accept_app_to_spotify_account()

    def accept_app_to_spotify_account(self):
        payload = {'scope': self.__scope,
                   'redirect_uri': self.__callback,
                   'response_type': 'code',
                   'client_id': self.__client_id,
                   'csrf_token': self.session.cookies.get('csrf_token')}
        response = self.session.post(ACCEPT_URL,
                                     data=payload,
                                     headers=HEADERS)
        return self.authenticate(response)

    def authenticate(self, response):
        code = response.json().get('redirect').split('code=')[1]
        payload = {'grant_type' : 'authorization_code',
                   'code': code,
                   'redirect_uri': self.__callback}
        base64encoded = b64encode("{}:{}".format(self.__client_id,
                                                 self.__client_secret))
        headers = {"Authorization": "Basic {}".format(base64encoded)}
        response = self.session.post(TOKEN_URL,
                                     data=payload,
                                     headers=headers)
        self.token = Token(response.json())
        return response

    @staticmethod
    def __get_bon(response_page):
        soup = Bfs(response_page, 'html.parser')
        meta = soup.find_all('meta')[-1]
        data = ast.literal_eval(meta.attrs.get('sp-bootstrap-data'))
        bon = data.get('BON')
        return bon

    @staticmethod
    def __calculate_bon(bon):
        bon.extend([bon[-1] * 42, 1, 1, 1, 1])
        __bon = b64encode('|'.join([str(entry) for entry in bon]))
        return __bon

    @staticmethod
    def __validate_bon(bon, cookie_bon):
        result = False
        if bon == int(cookie_bon.decode('base64').split('|')[2]):
            result = True
        return result


class Token(object):
    def __init__(self, token_details):
        self._token_details = token_details

    @property
    def access_token(self):
        return self._token_details.get('access_token', None)

    @property
    def token_type(self):
        return self._token_details.get('token_type', None)

    @property
    def expires_in(self):
        return self._token_details.get('expires_in', None)

    @property
    def refresh_token(self):
        return self._token_details.get('refresh_token', None)

    @property
    def scope(self):
        return self._token_details.get('scope', None)


if __name__ == '__main__':
    import os
    spotify = Spotify(client_id=os.environ.get('CLIENT_ID'),
                      client_secret=os.environ.get('CLIENT_SECRET'),
                      username=os.environ.get('USERNAME'),
                      password=os.environ.get('PASSWORD'),
                      callback=os.environ.get('CALLBACK_URL'),
                      scope=os.environ.get('SCOPE'))
    print(spotify.token.access_token)
