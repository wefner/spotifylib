============================
spotifylib
============================

Spotify API Client

This library aims to implement Spotify's `Authorization flow <https://developer.spotify.com/web-api/authorization-guide/#authorization_code_flow>`_
without the user needing to create a third party application to authorize the
application, redirect it to the callback and then manually authorize it with
username and password.

The user will only need to create an application under his/her `developer site <https://developer.spotify.com/my-applications/#!/applications>`_
and get `Client ID`, `Client Secret` and provide a `Redirect URI` - `http://127.0.0.1/callback` would just work.

Up until this point, the user will need to provide a `scope` to get a token that
has access to the resources. Read more about scopes `here <https://developer.spotify.com/web-api/using-scopes/>`_

Read more on `USAGE.rst`

Features
--------

* TODO
