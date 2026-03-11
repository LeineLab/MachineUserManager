# -*- coding: utf-8 -*-

"""
MakerSpaceAPI connector for MachineUserManager
"""

import time
import requests

import logging

logger = logging.getLogger(__name__)


class api:
    api_url = "http://localhost:8000"
    api_token = ""
    machine = "lasercutter"

    def configure(**kwargs):
        if "api_url" in kwargs:
            api.api_url = kwargs["api_url"].rstrip("/")
        if "api_token" in kwargs:
            api.api_token = kwargs["api_token"]
        if "machine" in kwargs:
            api.machine = kwargs["machine"]

    def _headers():
        return {"Authorization": f"Bearer {api.api_token}"}

    def _base():
        return f"{api.api_url}/api/v1"

    def __init__(self, uid):
        # uid may be an integer (raw NFC UID) or bytes
        if isinstance(uid, (bytes, bytearray)):
            n = 0
            for b in uid:
                n <<= 8
                n += b
            self.uid = n
        else:
            self.uid = uid

        self.per_login = 0
        self.per_minute = 0
        self.session_valid_until = 0
        self.credit = 0
        self._session_id = None
        self._name = None

        # Pre-fetch user info once on init
        try:
            r = requests.get(
                f"{api._base()}/users/nfc/{self.uid}",
                headers=api._headers(),
                timeout=5,
            )
            if r.ok:
                data = r.json()
                self._name = data.get("name")
                self.credit = float(data.get("balance", 0))
        except requests.RequestException:
            logger.exception("Could not fetch user info on init")

    def get_user_info(self):
        try:
            r = requests.get(
                f"{api._base()}/users/nfc/{self.uid}",
                headers=api._headers(),
                timeout=5,
            )
            if r.ok:
                data = r.json()
                self._name = data.get("name")
                self.credit = float(data.get("balance", 0))
                return self._name, self.credit
            return None, None
        except requests.RequestException:
            logger.exception("get_user_info failed")
            return None, None

    def get_rate(self, fallback_login, fallback_minute):
        try:
            r = requests.get(
                f"{api._base()}/machines/{api.machine}/authorize/{self.uid}",
                headers=api._headers(),
                timeout=5,
            )
            if r.ok:
                data = r.json()
                self.per_login = float(data.get("price_per_login", fallback_login))
                self.per_minute = float(data.get("price_per_minute", fallback_minute))
                return self.per_login, self.per_minute
            self.per_login = fallback_login
            self.per_minute = fallback_minute
            return None, None
        except requests.RequestException:
            logger.exception("get_rate failed")
            self.per_login = fallback_login
            self.per_minute = fallback_minute
            return None, None

    def is_authorized(self):
        try:
            r = requests.get(
                f"{api._base()}/machines/{api.machine}/authorize/{self.uid}",
                headers=api._headers(),
                timeout=5,
            )
            if r.ok:
                return r.json().get("authorized", False)
            return False
        except requests.RequestException:
            logger.exception("is_authorized failed")
            return False

    def can_create_session(self):
        price = self.per_login + self.per_minute
        self.check_credit()
        return self.credit >= price

    def check_credit(self):
        try:
            r = requests.get(
                f"{api._base()}/users/nfc/{self.uid}",
                headers=api._headers(),
                timeout=5,
            )
            if r.ok:
                self.credit = float(r.json().get("balance", 0))
                return self.credit
            return 0
        except requests.RequestException:
            logger.exception("check_credit failed")
            return 0

    def create_session(self, fallback_login, fallback_minute):
        self.start_time = int(time.time())
        self.get_rate(fallback_login, fallback_minute)
        try:
            r = requests.post(
                f"{api._base()}/sessions",
                headers=api._headers(),
                json={"nfc_id": self.uid},
                timeout=5,
            )
            if r.ok:
                data = r.json()
                self._session_id = data.get("session_id")
                self.check_credit()
                self.session_valid_until = self.start_time + 60
                return True
            return False
        except requests.RequestException:
            logger.exception("create_session failed")
            return False

    """
    Check if current session is still valid and extend if necessary.
    Returns True if still valid or revaluation was successful.
    Returns False if no session was created beforehand or credit is not enough to extend.
    """

    def extend_session(self):
        if self._session_id is None:
            return False
        if self.session_valid_until >= time.time():
            return True
        try:
            r = requests.put(
                f"{api._base()}/sessions/{self._session_id}",
                headers=api._headers(),
                timeout=5,
            )
            if r.ok:
                self.check_credit()
                self.session_valid_until += 60
                return True
            # 402 = insufficient balance → session terminated by API
            return False
        except requests.RequestException:
            logger.exception("extend_session failed")
            return False

    def get_remaining_time(self):
        if self.per_minute is None:
            return 0
        elif self.per_minute == 0:
            return 999
        else:
            return int(
                (self.credit - (self.per_login if self.session_valid_until == 0 else 0))
                / self.per_minute
            )

    def end_session(self):
        if self._session_id is None:
            return
        try:
            requests.delete(
                f"{api._base()}/sessions/{self._session_id}",
                headers=api._headers(),
                timeout=5,
            )
        except requests.RequestException:
            logger.exception("end_session failed")
        self.session_valid_until = 0
        self._session_id = None
