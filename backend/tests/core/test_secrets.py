import base64

import pytest

from app.core.secrets import open_secret, seal_secret


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def test_seal_secret_round_trips() -> None:
    sealed = seal_secret(
        "statement-password",
        secret_key="local-test-secret",
    )

    assert sealed != "statement-password"
    assert open_secret(
        sealed,
        secret_key="local-test-secret",
    ) == "statement-password"


def test_open_secret_rejects_tampered_payload() -> None:
    sealed = seal_secret(
        "statement-password",
        secret_key="local-test-secret",
    )
    version, encoded_nonce, encoded_ciphertext, encoded_tag = sealed.split(".", 3)
    tampered_tag = bytearray(_b64url_decode(encoded_tag))
    tampered_tag[0] ^= 0x01
    tampered = ".".join(
        (
            version,
            encoded_nonce,
            encoded_ciphertext,
            _b64url_encode(bytes(tampered_tag)),
        )
    )

    with pytest.raises(ValueError, match="Invalid sealed secret"):
        open_secret(tampered, secret_key="local-test-secret")
