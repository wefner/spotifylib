=====
Usage
=====

To use spotifylib in a project:

Instructions
------------
Go to your account's `developer site <https://developer.spotify.com/my-applications/#!/applications>`_
and create an application. Give it a name and get the ``Client ID``, ``Client Secret``
and provide a ``Redirect URI`` - ``http://127.0.0.1/callback`` would just work.

You will also need to use a ``scope`` to get a token that has access to the resources.
Read more about scopes `here <https://developer.spotify.com/web-api/using-scopes/>`_

Scopes can be appended by using a white space. Let's assume we will use
``playlist-modify-public playlist-modify-private`` as ``scope``.


.. code-block:: bash

    $ pip install spotifylib

.. code-block:: python

    from spotifylib import Spotify
    import logging
    import os

    logging.basicConfig(level=logging.DEBUG)

    # As soon as we instantiate, it runs the authentication flow and get
    # the token to communicate with the API.
    spotify = Spotify(client_id=os.environ.get('CLIENT_ID'),
                      client_secret=os.environ.get('CLIENT_SECRET'),
                      username=os.environ.get('USERNAME'),
                      password=os.environ.get('PASSWORD'),
                      callback=os.environ.get('CALLBACK_URL'),
                      scope=os.environ.get('SCOPE'))
    DEBUG:urllib3.connectionpool:Starting new HTTPS connection (1): accounts.spotify.com
    DEBUG:urllib3.connectionpool:https://accounts.spotify.com:443 "GET /en/authorize?scope=<SCOPE>&redirect_uri=<CALLBACK>&response_type=code&client_id=<CLIENT_ID> HTTP/1.1" 200 None
    DEBUG:urllib3.connectionpool:https://accounts.spotify.com:443 "POST /api/login HTTP/1.1" 200 None
    DEBUG:urllib3.connectionpool:https://accounts.spotify.com:443 "POST /en/authorize/accept HTTP/1.1" 200 None
    DEBUG:urllib3.connectionpool:https://accounts.spotify.com:443 "POST /api/token HTTP/1.1" 200 None

    # Using Spotipy's method to retrieve user's playlist.
    # Note that the patch method is used to validate the token expiration
    playlists = spotify.user_playlists(os.environ.get('USERNAME'))
    DEBUG:spotifylib.SpotifyAuthenticator:Using patched request for method GET, url https://api.spotify.com/v1/users/<username>/playlists
    DEBUG:urllib3.connectionpool:Starting new HTTPS connection (1): api.spotify.com
    DEBUG:urllib3.connectionpool:https://api.spotify.com:443 "GET /v1/users/<username>/playlists?limit=50&offset=0 HTTP/1.1" 200 None

    # If the token has expired, the patched request will request a new token
    # from the refresh token
    user_details = spotify.me()
    DEBUG:spotifylib.SpotifyAuthenticator:Using patched request for method GET, url https://api.spotify.com/v1/me/
    DEBUG:urllib3.connectionpool:Starting new HTTPS connection (1): api.spotify.com
    DEBUG:urllib3.connectionpool:https://api.spotify.com:443 "GET /v1/me/ HTTP/1.1" 401 None
    WARNING:spotifylib.SpotifyAuthenticator:Expired token detected, trying to refresh!
    DEBUG:spotifylib.SpotifyAuthenticator:Using patched request for method POST, url https://accounts.spotify.com/api/token
    DEBUG:urllib3.connectionpool:Starting new HTTPS connection (1): accounts.spotify.com
    DEBUG:urllib3.connectionpool:https://accounts.spotify.com:443 "POST /api/token HTTP/1.1" 200 None
    DEBUG:spotifylib.SpotifyAuthenticator:Updated headers, trying again initial request
    DEBUG:urllib3.connectionpool:https://api.spotify.com:443 "GET /v1/me/ HTTP/1.1" 200 None


Your linked app can then be found under `user's profile <https://www.spotify.com/nl/account/apps/>`_
