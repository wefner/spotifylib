"""
defines constants

Static URL's and variables
"""

from urlparse import urlparse

SITE = 'https://accounts.spotify.com'
AUTHORIZE_URL = '{SITE}/authorize'.format(SITE=SITE)
API_LOGIN_URL = '{SITE}/api/login'.format(SITE=SITE)
LOGIN_WEB_URL = '{SITE}/en/login'.format(SITE=SITE)
AUTHORIZE_WEB_URL = '{SITE}/en/authorize'.format(SITE=SITE)
ACCEPT_URL = '{SITE}/en/authorize/accept'.format(SITE=SITE)
TOKEN_URL = '{SITE}/api/token'.format(SITE=SITE)

HEADERS = {'Host': urlparse(SITE).netloc,
           'Accept': 'application/json, text/plain, */*',
           'Content-Type': 'application/x-www-form-urlencoded'}
