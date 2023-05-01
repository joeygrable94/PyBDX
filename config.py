from os import environ
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()

# SSH host vars
CLIENT_NAME: str = environ.get('SITE_NAME', 'Client Name')
SITE_ROOT: str = environ.get('SITE_ROOT', 'clientsite')
SITE_TLD: str = environ.get('SITE_TLD', 'com')
SITE_IP: str = environ.get('SITE_IP', '127.0.0.1')
SSH_TIMEOUT_MS: int = 500
SSH_HOST: str = '%s.%s' % ( SITE_ROOT, SITE_TLD )
SSH_PORT: str = environ.get('SSH_PORT', '22')
SSH_USER: str = environ.get('SSH_USER', 'username')
SSH_PASS: str = environ.get('SSH_PASS', 'password')
DEFAULT_EMAIL: str = environ.get('DEFAULT_EMAIL', 'email@company.com')

# BDX vars
BDX_FEED_XML_FILE_ID: str = environ.get('BDX_FEED_XML_FILE_ID')
BDX_SERVERHOST: str = environ.get('BDX_SERVERHOST')
BDX_USERNAME: str = environ.get('BDX_USERNAME')
BDX_PASSWORD: str = environ.get('BDX_PASSWORD')
BDX_SERVER_PATH: str = 'ftp://%s:%s@%s' % (BDX_USERNAME, BDX_PASSWORD, BDX_SERVERHOST)

NAME_FILTER_LIST: List[str] | List = []

# Wordpress Builder CPT IDs
WP_CPT_SLUG_ID: Dict[str, str] = {
	'wordpress-slug-name': '115',
}
