"""
defines constants

Static URL's and variables
"""

from urlparse import urlparse

SITE = 'https://accounts.spotify.com'
AUTH_API_URL = '{SITE}/authorize'.format(SITE=SITE)
API_LOGIN_URL = '{SITE}/api/login'.format(SITE=SITE)
LOGIN_WEB_URL = '{SITE}/en/login'.format(SITE=SITE)
AUTH_WEB_URL = '{SITE}/en/authorize'.format(SITE=SITE)
ACCEPT_URL = '{AUTH_URL}/accept'.format(AUTH_URL=AUTH_WEB_URL)
TOKEN_URL = '{SITE}/api/token'.format(SITE=SITE)

HEADERS = {'Host': urlparse(SITE).netloc,
           'Accept': 'application/json, text/plain, */*',
           'Content-Type': 'application/x-www-form-urlencoded'}

