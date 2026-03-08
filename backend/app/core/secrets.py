import base64
import hashlib
import hmac
import secrets

_SEALED_SECRET_VERSION = "v1"
_NONCE_BYTES = 16


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def _derive_subkey(secret_key: str, *, context: bytes) -> bytes:
    return hmac.new(secret_key.encode("utf-8"), context, hashlib.sha256).digest()


def _keystream(*, key: bytes, nonce: bytes, length: int) -> bytes:
    chunks: list[bytes] = []
    counter = 0
    generated = 0
    while generated < length:
        block = hmac.new(
            key,
            nonce + counter.to_bytes(4, "big"),
            hashlib.sha256,
        ).digest()
        chunks.append(block)
        generated += len(block)
        counter += 1
    return b"".join(chunks)[:length]


def _xor_bytes(left: bytes, right: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(left, right, strict=True))


def seal_secret(value: str, *, secret_key: str) -> str:
    if not value:
        raise ValueError("Secret value is required")

    plaintext = value.encode("utf-8")
    nonce = secrets.token_bytes(_NONCE_BYTES)
    encryption_key = _derive_subkey(
        secret_key,
        context=b"statement-password-encryption",
    )
    authentication_key = _derive_subkey(
        secret_key,
        context=b"statement-password-authentication",
    )
    ciphertext = _xor_bytes(
        plaintext,
        _keystream(key=encryption_key, nonce=nonce, length=len(plaintext)),
    )
    tag = hmac.new(
        authentication_key,
        nonce + ciphertext,
        hashlib.sha256,
    ).digest()
    return ".".join(
        (
            _SEALED_SECRET_VERSION,
            _b64url_encode(nonce),
            _b64url_encode(ciphertext),
            _b64url_encode(tag),
        )
    )


def open_secret(token: str, *, secret_key: str) -> str:
    try:
        version, encoded_nonce, encoded_ciphertext, encoded_tag = token.split(".", 3)
    except ValueError as exc:
        raise ValueError("Malformed sealed secret") from exc

    if version != _SEALED_SECRET_VERSION:
        raise ValueError("Unsupported sealed secret version")

    try:
        nonce = _b64url_decode(encoded_nonce)
        ciphertext = _b64url_decode(encoded_ciphertext)
        provided_tag = _b64url_decode(encoded_tag)
    except (TypeError, ValueError) as exc:
        raise ValueError("Malformed sealed secret") from exc

    authentication_key = _derive_subkey(
        secret_key,
        context=b"statement-password-authentication",
    )
    expected_tag = hmac.new(
        authentication_key,
        nonce + ciphertext,
        hashlib.sha256,
    ).digest()
    if not hmac.compare_digest(provided_tag, expected_tag):
        raise ValueError("Invalid sealed secret")

    encryption_key = _derive_subkey(
        secret_key,
        context=b"statement-password-encryption",
    )
    plaintext = _xor_bytes(
        ciphertext,
        _keystream(key=encryption_key, nonce=nonce, length=len(ciphertext)),
    )
    try:
        return plaintext.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Malformed sealed secret") from exc
