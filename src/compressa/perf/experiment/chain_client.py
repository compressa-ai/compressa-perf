
import time
import json
import hashlib
import base64
from typing import List
import contextlib
import os
import resource

import requests
import urllib3
from ecdsa import SigningKey, SECP256k1, util

from compressa.utils import get_logger

logger = get_logger(__name__)


def check_system_limits():
    """Check and log system limits for file descriptors"""
    try:
        soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
        logger.info(f"File descriptor limits: soft={soft_limit}, hard={hard_limit}")
        
        # Warn if limits are too low
        if soft_limit < 10000:
            logger.warning(f"Low file descriptor limit ({soft_limit}). Consider increasing with 'ulimit -n 65536'")
        
        return soft_limit, hard_limit
    except Exception as e:
        logger.error(f"Could not check system limits: {e}")
        return None, None


# ---------------------------------------------------------------------------
# High-performance HTTP client optimized for concurrent requests
# ---------------------------------------------------------------------------
class _NodeClient:
    def __init__(
        self,
        node_url: str,
        account_address: str = None,
        private_key_hex: str = None,
        timeout: float = 600.0,
        max_connections: int = 100,  # Reduced from 1000
        max_connections_per_host: int = 100,  # Reduced from 1000  
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        no_sign: bool = False,
    ) -> None:
        self.node_url = node_url.rstrip("/")
        self.account_address = account_address
        self.timeout = timeout
        self.no_sign = no_sign

        # Check system limits on first initialization
        if not hasattr(_NodeClient, '_limits_checked'):
            check_system_limits()
            _NodeClient._limits_checked = True

        # Deterministic signing key (only if signing is enabled)
        if not self.no_sign:
            if not account_address:
                raise ValueError("account_address is required when signing is enabled")
            if not private_key_hex:
                raise ValueError("private_key_hex is required when signing is enabled")
            self._signing_key = SigningKey.from_string(
                bytes.fromhex(private_key_hex), curve=SECP256k1
            )

        # Configure urllib3 for high performance
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Create optimized session for high concurrency
        self._session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = urllib3.util.Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"],
            raise_on_status=False  # Don't raise on retry-able status codes
        )
        
        # Configure HTTP adapter with conservative settings for stability
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=max_connections,
            pool_maxsize=max_connections_per_host,
            max_retries=retry_strategy,
            pool_block=True  # Block when pool is full instead of creating new connections
        )
        
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)
        
        # Configure session defaults for better performance and connection reuse
        self._session.headers.update({
            'Connection': 'keep-alive',
            'Keep-Alive': 'timeout=30, max=1000'
        })

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Properly close the session and clean up resources"""
        if hasattr(self, '_session'):
            try:
                self._session.close()
            except Exception as e:
                logger.debug(f"Error closing session: {e}")

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


# ---------------------------------------------------------------------------
# Optimized client manager for high-concurrency scenarios
# ---------------------------------------------------------------------------
class OptimizedNodeClientManager:
    """
    Manages a pool of _NodeClient instances to handle high-concurrency requests.
    This helps distribute load across multiple connection pools.
    """
    
    def __init__(
        self,
        node_url: str,
        account_address: str = None,
        private_key_hex: str = None,
        timeout: float = 600.0,
        num_clients: int = 5,  # Reduced from 10
        max_connections_per_client: int = 50,  # Reduced from 500
        no_sign: bool = False,
    ):
        self.clients = []
        self.current_client_index = 0
        
        logger.info(f"Creating {num_clients} optimized HTTP clients with {max_connections_per_client} connections each")
        
        for _ in range(num_clients):
            client = _NodeClient(
                node_url=node_url,
                account_address=account_address,
                private_key_hex=private_key_hex,
                timeout=timeout,
                max_connections=max_connections_per_client,
                max_connections_per_host=max_connections_per_client,
                max_retries=3,
                backoff_factor=0.5,
                no_sign=no_sign,
            )
            self.clients.append(client)
    
    def get_client(self) -> _NodeClient:
        """Get the next client using round-robin selection"""
        client = self.clients[self.current_client_index]
        self.current_client_index = (self.current_client_index + 1) % len(self.clients)
        return client
    
    def close_all(self):
        """Close all clients"""
        for client in self.clients:
            client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_all()


# ---------------------------------------------------------------------------
# Streaming response wrapper for proper resource cleanup
# ---------------------------------------------------------------------------
@contextlib.contextmanager
def managed_stream_response(response):
    """Context manager for properly handling streaming responses"""
    try:
        yield response
    finally:
        # Ensure response is properly closed
        try:
            if hasattr(response, 'close'):
                response.close()
            # Also close the underlying connection if needed
            if hasattr(response, 'raw') and hasattr(response.raw, 'close'):
                response.raw.close()
        except Exception as e:
            logger.debug(f"Error during response cleanup: {e}")  # Don't fail on cleanup errors
