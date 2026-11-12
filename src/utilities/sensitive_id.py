"""Encryption and duplicate-detection for government identifiers (BVN, NIN).

These were stored as bare plaintext strings carrying unique=True, while wallet
balances -- far less sensitive -- were encrypted. GET /kycs returned them in
full to any authenticated caller, so one request read every customer's BVN.

They are now encrypted at rest. Fernet is non-deterministic, so the ciphertext
cannot carry a unique constraint: the same BVN encrypts differently every time
and the database would accept it twice. Uniqueness therefore moves to a keyed
HMAC of the value -- stable for a given input, and useless to anyone who does
not hold the secret, so it cannot be reversed with a dictionary of the ~10^11
possible BVNs the way a bare SHA-256 could.
"""
import hashlib
import hmac

import config

from .cryptographer import Cryptographer


def _clean(value):
    """Normalise before encrypting or hashing, so the hash is stable."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def encrypt_identifier(value):
    """Encrypt an identifier for storage. None and blank pass through as None."""
    text = _clean(value)

    if text is None:
        return None

    return Cryptographer.encrypt(text)


def decrypt_identifier(token):
    """Return the plaintext identifier.

    Tolerates a legacy plaintext row. Values written before encryption are
    bare digits, and raising on those would take account provisioning down
    rather than merely failing to read an old record.
    """
    if token is None:
        return None

    raw = str(token).strip()

    if not raw:
        return None

    try:
        return Cryptographer.decrypt(raw)
    except Exception:
        # Written before this module existed, so it is already plaintext.
        # Only digits qualify: anything else is a genuinely broken value and
        # must not be handed to the bank as though it were an identifier.
        return raw if raw.isdigit() else None


def hash_identifier(value):
    """Keyed digest used to enforce uniqueness without storing plaintext."""
    text = _clean(value)

    if text is None:
        return None

    return hmac.new(
        config.secret_key.encode(), text.encode(), hashlib.sha256).hexdigest()
