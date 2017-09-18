=====
Usage
=====

To use spotifylib in a project:

.. code-block:: python


    from spotifylib import Spotify
    import os

    spotify = Spotify(client_id=os.environ.get('CLIENT_ID'),
                      client_secret=os.environ.get('CLIENT_SECRET'),
                      username=os.environ.get('USERNAME'),
                      password=os.environ.get('PASSWORD'),
                      callback=os.environ.get('CALLBACK_URL'),
                      scope=os.environ.get('SCOPE'))
    print(spotify.token.access_token)
