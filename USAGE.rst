=====
Usage
=====

To use spotifylib in a project:

Instructions
------------
Go to your account's `developer site <https://developer.spotify.com/my-applications/#!/applications>`_
and create an application. Give it a name and get the `Client ID`, `Client Secret`
and provide a `Redirect URI` - `http://127.0.0.1/callback` would just work.

You will also need to use a `scope` to get a token that has access to the resources.
Read more about scopes `here <https://developer.spotify.com/web-api/using-scopes/>`_

Scopes can be appended by using a white space. Let's assume we will use
`playlist-modify-public playlist-modify-private` as `scope`.


.. code-block:: bash

    $ pip install spotifylib

.. code-block:: python


    from spotifylib import Spotify
    import os

    spotify = Spotify(client_id=os.environ.get('CLIENT_ID'),
                      client_secret=os.environ.get('CLIENT_SECRET'),
                      username=os.environ.get('USERNAME'),
                      password=os.environ.get('PASSWORD'),
                      callback=os.environ.get('CALLBACK_URL'),
                      scope=os.environ.get('SCOPE'))
    print(spotify.user_playlists(os.environ.get('USERNAME')))


Your linked app can then be found under `user's profile <https://www.spotify.com/nl/account/apps/>`_
