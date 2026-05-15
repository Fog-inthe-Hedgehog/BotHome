"""Parse Telegram MTProto proxy URLs (tg://proxy?...)."""

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

    return MtprotoProxyConfig(server=server, port=port, secret=secret)


def _required_param(params: dict[str, list[str]], name: str) -> str:
    values = params.get(name)
    if not values or not values[0].strip():
        raise ValueError(f"Missing MTProto proxy parameter: {name}")
    return values[0].strip()


def mtproxy_connection_class(secret: str):
    if secret.startswith("ee"):
        return connection.ConnectionTcpMTProxyRandomizedIntermediate
    if secret.startswith("dd"):
        return connection.ConnectionTcpMTProxyIntermediate
    return connection.ConnectionTcpMTProxyRandomizedIntermediate
