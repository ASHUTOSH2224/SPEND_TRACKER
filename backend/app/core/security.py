import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any


class TokenValidationError(Exception):
    pass


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def hash_password(password: str, *, iterations: int) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${_b64url_encode(salt)}${_b64url_encode(digest)}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        scheme, raw_iterations, salt_value, digest_value = password_hash.split("$", 3)
    except ValueError:
        return False

    if scheme != "pbkdf2_sha256":
        return False

    try:
        iterations = int(raw_iterations)
        salt = _b64url_decode(salt_value)
        expected_digest = _b64url_decode(digest_value)
    except (TypeError, ValueError):
        return False

    actual_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual_digest, expected_digest)


def create_access_token(
    *,
    subject: str,
    secret_key: str,
    algorithm: str,
    expires_delta: timedelta,
    now: datetime | None = None,
) -> str:
    if algorithm != "HS256":
        raise ValueError("Only HS256 JWT signing is supported")

    issued_at = now or datetime.now(UTC)
    expires_at = issued_at + expires_delta
    payload = {
        "sub": subject,
        "type": "access",
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    header = {"alg": algorithm, "typ": "JWT"}

    encoded_header = _b64url_encode(
        json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    encoded_payload = _b64url_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signing_input = f"{encoded_header}.{encoded_payload}"
    signature = hmac.new(
        secret_key.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def decode_access_token(
    token: str,
    *,
    secret_key: str,
    algorithm: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    if algorithm != "HS256":
        raise TokenValidationError("Unsupported JWT algorithm")

    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".")
    except ValueError as exc:
        raise TokenValidationError("Malformed JWT") from exc

    signing_input = f"{encoded_header}.{encoded_payload}"
    expected_signature = hmac.new(
        secret_key.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()

    try:
        provided_signature = _b64url_decode(encoded_signature)
        header = json.loads(_b64url_decode(encoded_header))
        payload = json.loads(_b64url_decode(encoded_payload))
    except (ValueError, json.JSONDecodeError) as exc:
        raise TokenValidationError("Malformed JWT") from exc

    if not hmac.compare_digest(provided_signature, expected_signature):
        raise TokenValidationError("Invalid JWT signature")

    if header.get("alg") != algorithm or header.get("typ") != "JWT":
        raise TokenValidationError("Invalid JWT header")

    if payload.get("type") != "access":
        raise TokenValidationError("Invalid token type")

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise TokenValidationError("JWT subject is missing")

    expires_at = payload.get("exp")
    if not isinstance(expires_at, int):
        raise TokenValidationError("JWT expiration is missing")

    current_time = int((now or datetime.now(UTC)).timestamp())
    if expires_at <= current_time:
        raise TokenValidationError("JWT has expired")

    return payload
