import json
from functools import lru_cache
from os import environ
from typing import Dict, List

from dotenv import load_dotenv
from pydantic import BaseConfig, validator

load_dotenv()


class CLIENT(BaseConfig):
    # SSH host vars
    CLIENT_NAME: str = environ.get("CLIENT_NAME", "Client Name")
    SITE_ROOT: str = environ.get("SITE_ROOT", "clientsite")
    SITE_TLD: str = environ.get("SITE_TLD", "com")
    SITE_IP: str = environ.get("SITE_IP", "127.0.0.1")
    SSH_TIMEOUT_MS: int = 500
    SSH_HOST: str = "%s.%s" % (SITE_ROOT, SITE_TLD)
    SSH_PORT: str = environ.get("SSH_PORT", "22")
    SSH_USER: str = environ.get("SSH_USER", "username")
    SSH_PASS: str = environ.get("SSH_PASS", "password")
    DEFAULT_EMAIL: str = environ.get("DEFAULT_EMAIL", "email@company.com")

    # BDX vars
    BDX_FEED_XML_FILE_ID: str = environ.get("BDX_FEED_XML_FILE_ID", "")
    @validator("BDX_FEED_XML_FILE_ID")
    def validate_bdx_feed_xml_file_id(cls, value):
        if value is None or len(value) == 0:
            raise ValueError("BDX_FEED_XML_FILE_ID is not set")
        return value
    
    BDX_SERVERHOST: str = environ.get("BDX_SERVERHOST", "")
    @validator("BDX_SERVERHOST")
    def validate_bdx_serverhost(cls, value):
        if value is None or len(value) == 0:
            raise ValueError("BDX_SERVERHOST is not set")
        return value

    BDX_USERNAME: str = environ.get("BDX_USERNAME", "")
    @validator("BDX_USERNAME")
    def validate_bdx_username(cls, value):
        if value is None or len(value) == 0:
            raise ValueError("BDX_USERNAME is not set")
        return value
    
    BDX_PASSWORD: str = environ.get("BDX_PASSWORD", "")
    @validator("BDX_PASSWORD")
    def validate_bdx_password(cls, value):
        if value is None or len(value) == 0:
            raise ValueError("BDX_PASSWORD is not set")
        return value
    
    BDX_SERVER_PATH: str = environ.get("BDX_SERVER_PATH", "")
    @validator("BDX_SERVER_PATH")
    def validate_bdx_server_path(cls, values):
        bdx_pass = "ftp://%s:%s@%s" % (
            values.get('BDX_USERNAME'),
            values.get('BDX_PASSWORD'),
            values.get('BDX_SERVERHOST'),
        )
        return bdx_pass

    # Report Automation
    REPORT_AUTOMATION_WEBHOOK: str = environ.get("REPORT_AUTOMATION_WEBHOOK", "")
    @validator("REPORT_AUTOMATION_WEBHOOK")
    def validate_report_automation_webhook(cls, value):
        if value is None or len(value) == 0:
            raise ValueError("REPORT_AUTOMATION_WEBHOOK is not set")
        return value

    # Filters
    NAME_FILTER_LIST: List[str] | List = (
        environ.get("NAME_FILTER_LIST", "[]")
        .replace("\n", "")
        .replace("\r", "")
        .replace("\t", "")
        .replace("'", "")
        .strip("][")
        .split(",")
    )

    # WP ID Tagging
    WP_CPT_SLUG_ID: Dict[str, str] = json.loads(environ.get("WP_CPT_SLUG_ID", "{}"))


@lru_cache
def get_client() -> CLIENT:
    return CLIENT()
