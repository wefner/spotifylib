============
Introduction
============

Spotify API Client

This library aims to implement Spotify's `Authorization flow <https://developer.spotify.com/web-api/authorization-guide/#authorization_code_flow>`_
without the user needing to create a third party application to authorize the
application, redirect it to the callback and then manually authorize it with
username and password.

This library goal is to make authorization transparent but using `Spotipy's <http://spotipy.readthedocs.io/en/latest/>`_
functionality. It is implemented in a non-standard way that Spotify wouldn't
recommend so we can't guarantee this would work forever.

Read more on `USAGE.rst <https://github.com/wefner/spotifylib/blob/master/USAGE.rst>`_
or `Read the docs <http://spotifylib.readthedocs.io/en/latest/>`_
or check the code for substantial docstrings.


How does the library work
-------------------------

.. image:: https://image.ibb.co/ekaugG/spotifylib_authorization_flow_Page_1_2.png
   :scale: 70%
   :align: center
   :height: 1500px
   :width: 1200px


Features
--------

* Same features as Spotipy's library but with transparent authentication
* Renew's the token transparently

