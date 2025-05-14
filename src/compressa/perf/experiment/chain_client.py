
import time
import json
import hashlib
import base64
from typing import List

import requests
from ecdsa import SigningKey, SECP256k1, util

from compressa.utils import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Low‑level HTTP client that speaks to the inference node
# ---------------------------------------------------------------------------
class _NodeClient:
    def __init__(
        self,
        node_url: str,
        account_address: str = None,
        private_key_hex: str = None,
        timeout: float = 600.0,
        max_connections: int = 200,
        no_sign: bool = False,
    ) -> None:
        self.node_url = node_url.rstrip("/")
        self.account_address = account_address
        self.timeout = timeout
        self.no_sign = no_sign

        # Deterministic signing key (only if signing is enabled)
        if not self.no_sign:
            if not account_address:
                raise ValueError("account_address is required when signing is enabled")
            if not private_key_hex:
                raise ValueError("private_key_hex is required when signing is enabled")
            self._signing_key = SigningKey.from_string(
                bytes.fromhex(private_key_hex), curve=SECP256k1
            )

        # Connection‑pooled requests session
        self._session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=max_connections, pool_maxsize=max_connections
        )
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    def _sign(self, payload: bytes) -> str:
        """Return a *low‑s* canonical ECDSA signature encoded in base‑64."""
        raw_sig = self._signing_key.sign_deterministic(
            payload, hashfunc=hashlib.sha256, sigencode=util.sigencode_string
        )
        r, s = raw_sig[:32], raw_sig[32:]

        # Force *low‑s* form to avoid malleable sigs
        curve_n = SECP256k1.order
        s_int = int.from_bytes(s, "big")
        if s_int > curve_n // 2:
            s_int = curve_n - s_int
            s = s_int.to_bytes(32, "big")

        return base64.b64encode(r + s).decode()

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def stream_chat_completion(
        self,
        *,
        messages: List[dict],
        model: str,
        max_tokens: int,
        temperature: float = 0.8,
    ):
        """Send a streaming chat/completions request and return the raw response."""
        payload = {
            "temperature": temperature,
            "model": model,
            "messages": messages,
            "stream": True,
            "max_tokens": max_tokens,
            "stream_options": {
                "include_usage": True
            }
        }
        payload_bytes = json.dumps(payload, separators=(",", ":")).encode()

        headers = {
            "Content-Type": "application/json",
        }

        if not self.no_sign:
            headers["Authorization"] = self._sign(payload_bytes)
            headers["X-Requester-Address"] = self.account_address

        resp = self._session.post(
            f"{self.node_url}/v1/chat/completions",
            data=payload_bytes,
            headers=headers,
            stream=True,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp  # caller iterates resp.iter_lines(...)
