"""Parse Telegram MTProto proxy URLs (tg://proxy?...)."""

import base64
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from telethon import connection


@dataclass(frozen=True)
class MtprotoProxyConfig:
    server: str
    port: int
    secret: str


def parse_mtproto_proxy(proxy_url: str) -> MtprotoProxyConfig:
    proxy_url = proxy_url.strip()
    if not proxy_url.startswith("tg://"):
        raise ValueError(
            "TELEGRAM_PROXY must be an MTProto link, for example: "
            "tg://proxy?server=1.2.3.4&port=8443&secret=ee36e2e7275"
        )

    parsed = urlparse(proxy_url)
    if parsed.netloc != "proxy":
        raise ValueError(f"Expected tg://proxy?..., got: {proxy_url!r}")

    params = parse_qs(parsed.query)
    server = _required_param(params, "server")
    port_raw = _required_param(params, "port")
    secret = _required_param(params, "secret")

    try:
        port = int(port_raw)
    except ValueError as exc:
        raise ValueError(f"Invalid proxy port: {port_raw!r}") from exc

    if port < 1 or port > 65535:
        raise ValueError(f"Proxy port out of range: {port}")

    validate_mtproto_secret(secret)

    return MtprotoProxyConfig(server=server, port=port, secret=secret)


def _required_param(params: dict[str, list[str]], name: str) -> str:
    values = params.get(name)
    if not values or not values[0].strip():
        raise ValueError(f"Missing MTProto proxy parameter: {name}")
    return values[0].strip()


def normalize_mtproto_secret(secret: str) -> bytes:
    """Same rules as Telethon TcpMTProxy.normalize_secret()."""
    if secret[:2] in ("ee", "dd"):
        secret = secret[2:]

    try:
        secret_bytes = bytes.fromhex(secret)
    except ValueError:
        padded = secret + "=" * (-len(secret) % 4)
        secret_bytes = base64.b64decode(padded.encode())

    return secret_bytes[:16]


def validate_mtproto_secret(secret: str) -> None:
    secret_bytes = normalize_mtproto_secret(secret)
    if len(secret_bytes) != 16:
        raise ValueError(
            "MTProto secret must decode to 16 bytes. "
            "Check the secret from your tg://proxy link."
        )


def mtproxy_connection_class(secret: str, mode: str | None = None):
    modes = {
        "abridged": connection.ConnectionTcpMTProxyAbridged,
        "intermediate": connection.ConnectionTcpMTProxyIntermediate,
        "randomized": connection.ConnectionTcpMTProxyRandomizedIntermediate,
    }

    if mode:
        normalized_mode = mode.strip().lower()
        if normalized_mode not in modes:
            raise ValueError(
                f"Unknown TELEGRAM_MTPROTO_MODE={mode!r}. "
                f"Use: {', '.join(modes)}"
            )
        return modes[normalized_mode]

    # dd-secrets require randomized intermediate (Telethon requirement).
    if secret.startswith("dd"):
        return connection.ConnectionTcpMTProxyRandomizedIntermediate

    # ee-secrets (fake-TLS) usually work with intermediate, not randomized.
    if secret.startswith("ee"):
        return connection.ConnectionTcpMTProxyIntermediate

    return connection.ConnectionTcpMTProxyIntermediate
