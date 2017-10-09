#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
# File: spotifylib.py

"""
This module makes use of Spotipy's methods but modifying the authentication in
a simple and transparent way from the user without any need of 3rd party
application to follow the OAuth flow as mentioned in the following documentation
page.

https://developer.spotify.com/web-api/authorization-guide/#authorization_code_flow
"""

from requests import Session
from urllib import quote
from base64 import b64encode
from constants import *
from collections import namedtuple
from spotipy import Spotify as OriginalSpotify
from spotifylibexceptions import SpotifyError

import logging


__author__ = '''Oriol Fabregas <fabregas.oriol@gmail.com>'''
__credits__ = ['Costas Tyfoxylos', 'Oriol Fabregas']
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
    """
    Authenticator object

    This object handles authentication for all requests. In order to retrieve
    all values for this to work, one has to create a new application under
    his/her account.

    https://developer.spotify.com/my-applications/#!/applications
    """
    def __init__(self,
                 client_id,
                 client_secret,
                 username,
                 password,
                 callback,
                 scope):
        """
        Initialises object with credentials to perform the authentication

        :param client_id: string
        :param client_secret: string
        :param username: string
        :param password: string
        :param callback: string
        :param scope: string
        """
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

    def _get_referer(self):
        """
        Constructs the Referer header string.

        Instead of using one string and formatting all arguments, it creates
        2 tuples and joins them accordingly.
        :return: string
        """
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

    @property
    def token(self):
        return self._token

    def __authenticate(self):
        """
        Runs authentication process

        Performs all the steps described in the API documentation and then
        patches every request to verify if the token is still valid.

        :return: boolean
        """
        self._get_authorization()
        self._login_to_account()
        response = self._accept_app_to_account()
        self._token = self._get_token(response)
        self._monkey_patch_session()
        return True

    def _get_authorization(self):
        """
        Retrieves the landing page to request authorization

        This is the very first step mentioned in Spotify's API documentation.
        The difference is that this method already has the Referer in the
        headers which helps us retrieving the BON value.

        It then adds a "__bon_cookie" in the Session with its value.

        :return: boolean
        """
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

    @staticmethod
    def __get_bon(response):
        """
        Calculates BON value for authentication cookie

        This is a value that is received from the first authorization form and
        it is needed to be calculated accordingly as it is a required Cookie.
        The browser calculates it by using JavaScript and this is a Python
        implementation.

        The value is retrieved from the initial GET response after requesting
        the authorization page with its headers. The page will then provide a
        JSON content with the value needed as input for the algorithm.

        The way it works is that it multiplies by 42 the last integer in the
        list and it then appends four integers with a value of 1.

        After this operation, it creates a string with every value separated by
        "|" and it finally encodes it in base64.

        Example:
        -------
            - {u'country': u'NL',
               u'client': {u'name': u'fooapp'},
               u'BON': [u'0', u'0', -33232342],
               u'locales': [u'*']}

        :param response: Response instance
        :return: b64encoded string
        """
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
        """
        Logs the user in Spotify after requesting access for the APP.

        This is the second step in the documentation

        :return: boolean
        """
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

    def _accept_app_to_account(self):
        """
        Authorize access to the data sets defined in the scopes.

        This method is also part of the second step in the documentation
        but only used the first time when the application is not registered
        on the user's profile as approved application (URL below).

        https://www.spotify.com/nl/account/apps/

        When accepted, step 3 takes place and Spotify will return a code in the
        response to the specified redirect_url. This code will be required to
        request the token.

        :return: Response instance
        """
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
        """
        Retrieves token from code

        This is the 4th step in the authorization flow and it exchanges the code
        for a token. The token is the final value to interact with Spotify's API.

        :param response: Response instance
        :return: Token namedtuple
        """
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
        Get a new token from the last known refresh token

        As a token is only valid for 1 hour, the next response would fail with
        a 401 HTTP error as seen below. This method runs step 7 from authorization
        flow.

        Example:
        --------
        >>> response.json()
        {u'error': {u'status': 401, u'message': u'The access token expired'}}

        :param session: Session instance
        :param user: User namedtuple
        :return: Token namedtuple
        """
        payload = {'grant_type': 'refresh_token',
                   'refresh_token': token.refresh_token}
        return SpotifyAuthenticator._retrieve_token(session, user, payload)

    @staticmethod
    def _retrieve_token(session, user, payload):
        """
        Helper method to request and get the token

        As described in the fourth step from the authentication flow, the user
        needs to POST to /api/token accordingly with a body and headers.

        If the request is successful, it creates a Token namedtuple with its
        attributes to be accessed as objects.

        At this point the authorization flow is completed and we have reached
        step number 5. A user can use this token to interact with Spotify's API.

        :param session: Session object
        :param user: User namedtuple
        :param payload: dictionary
        :return: Token namedtuple
        """
        base64encoded = b64encode('{user_id}:{secret}'.format(user_id=user.client_id,
                                                              secret=user.client_secret))
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
        """
        Gets original request method and overrides it with the patched one

        It also sets Token and User namedtuples as well as the renew token
        method as session attributes.

        :return: Response instance
        """
        self.session.original_request = self.session.request
        self.session.token = self.token
        self.session.user = self.user
        self.session.renew_token = self._renew_token
        self.session.request = self._patched_request

    def _patched_request(self, method, url, **kwargs):
        """
        Patch the original request from Spotipy library if required.

        This method aims to validate if the session is still valid by first
        running the former request from Spotipy's and if not, retrieve a new
        token and try the request again.

        Spotipy's uses the following method to make HTTP requests so this
        patches it with the updated Session (auth, token, etc).

        https://github.com/plamere/spotipy/blob/master/spotipy/client.py#L97

        :param method: HTTP verb as string
        :param url: string
        :param kwargs: keyword arguments
        :return: Response instance
        """
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
    """
    Library's interface object

    Instantiates the authentication object to figure out the token and passes it
    alongside the session to Spotipy's in order to use its methods.
    """
    def __new__(cls,
                client_id,
                client_secret,
                username,
                password,
                callback,
                scope):
        """
        Initialises object and returns Spotipy's authenticated

        :param client_id: string
        :param client_secret: string
        :param username: string
        :param password: string
        :param callback: string
        :param scope: string
        :return: Spotipy object
        """
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
