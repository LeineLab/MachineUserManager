"""Background polling of a PN532 so the main loop never blocks on the reader.

The reader is only ever touched from the poller thread. The main loop calls
get() / get_int(), which return immediately with the most recently seen UID
(or None when no card is in the field).
"""

import logging
import threading
import time

from pn532pi import pn532

logger = logging.getLogger(__name__)

# Activation retries the PN532 itself performs per poll. 0xFF would make the
# chip wait forever, so a poll could neither be answered nor abandoned cleanly.
ACTIVATION_RETRIES = 0x02
# Upper bound in ms for one poll response (the library counts ~1 ms per try).
POLL_TIMEOUT_MS = 300
# A UID counts as "still present" for this long after it was last read.
MAX_AGE_S = 0.6
# Consecutive exceptions before the reader is re-initialised.
REINIT_AFTER_ERRORS = 5


class NfcPoller:
    def __init__(self, nfc):
        self._nfc = nfc
        self._lock = threading.Lock()
        self._uid = None
        self._seen = 0.0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="nfc-poller", daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=2)

    def get(self):
        """Return the UID bytes of the card currently in the field, or None."""
        with self._lock:
            if self._uid is not None and time.monotonic() - self._seen <= MAX_AGE_S:
                return bytearray(self._uid)
        return None

    def get_int(self):
        """Same as get(), but as big-endian integer (the API's card id)."""
        uid = self.get()
        if uid is None:
            return None
        value = 0
        for byte in uid:
            value = (value << 8) | byte
        return value

    def _init_reader(self):
        self._nfc.begin()
        self._nfc.setPassiveActivationRetries(ACTIVATION_RETRIES)
        self._nfc.SAMConfig()

    def _run(self):
        errors = 0
        while not self._stop.is_set():
            try:
                success, uid = self._nfc.readPassiveTargetID(
                    pn532.PN532_MIFARE_ISO14443A_106KBPS, timeout=POLL_TIMEOUT_MS
                )
                errors = 0
            except Exception:
                errors += 1
                logger.exception("NFC read failed (%d in a row)", errors)
                if errors >= REINIT_AFTER_ERRORS:
                    try:
                        self._init_reader()
                        logger.info("NFC reader re-initialised")
                        errors = 0
                    except Exception:
                        logger.exception("NFC reader re-initialisation failed")
                self._stop.wait(0.5)
                continue
            if success and len(uid) > 0:
                with self._lock:
                    self._uid = bytes(uid)
                    self._seen = time.monotonic()
            else:
                # Leave a short pause so an empty poll doesn't spin the bus.
                self._stop.wait(0.03)
