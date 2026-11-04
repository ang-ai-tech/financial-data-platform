"""HTTP session with retries and back-off for transient errors."""

from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_TIMEOUT_SECONDS = 30


def build_session(retries: int = 3, backoff_factor: float = 1.0) -> requests.Session:
    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers["User-Agent"] = "findata/0.1 (personal portfolio project)"
    return session


def get_text(
    session: requests.Session,
    url: str,
    params: dict[str, str] | None = None,
    *,
    empty_on_404: bool = False,
) -> str:
    """GET a text resource. Some APIs (e.g. ECB) answer 404 when a period has no data."""
    response = session.get(url, params=params, timeout=DEFAULT_TIMEOUT_SECONDS)
    if empty_on_404 and response.status_code == 404:
        return ""
    response.raise_for_status()
    return response.text
