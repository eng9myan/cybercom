"""
Thin VistaRPC broker client for Hakeem's MUMPS backend.

VistaRPC uses a text protocol over TCP: [XWB]<version>...[XWB]<command>...
Real deployments use pyVista-broker; this module wraps the essentials so
CyMed code can call `rpc('ORWPT ID INFO', args)` uniformly.

Ref: https://github.com/vistadataproject/pyVista (LGPL)
"""
from __future__ import annotations

import os
import socket
import time


class RpcError(RuntimeError):
    pass


class VistaRpcClient:
    def __init__(self, host: str | None = None, port: int | None = None,
                 access: str | None = None, verify: str | None = None,
                 timeout: int = 30):
        self.host = host or os.environ.get("HAKEEM_RPC_HOST", "")
        self.port = port or int(os.environ.get("HAKEEM_RPC_PORT", "9200"))
        self.access = access or os.environ.get("HAKEEM_RPC_ACCESS_CODE", "")
        self.verify = verify or os.environ.get("HAKEEM_RPC_VERIFY_CODE", "")
        self.timeout = timeout
        self._sock: socket.socket | None = None
        self._context: dict = {}

    # ── Framing helpers ─────────────────────────────────────────────────
    @staticmethod
    def _frame(command: str, body: str = "") -> bytes:
        # Simplified XWB framing: [XWB]11302{command}{body}\x04
        return f"[XWB]11302{command}{body}\x04".encode()

    def _connect(self):
        if self._sock:
            return
        s = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self._sock = s
        # Login
        self._raw("XWB CREATE CONTEXT", f"OR CPRS GUI CHART")
        self._raw("XUS SIGNON SETUP")
        self._raw("XUS AV CODE", f"{self.access};{self.verify}")

    def _raw(self, command: str, body: str = "") -> str:
        if not self._sock:
            raise RpcError("Not connected")
        self._sock.sendall(self._frame(command, body))
        buf = b""
        while True:
            chunk = self._sock.recv(4096)
            if not chunk:
                break
            buf += chunk
            if buf.endswith(b"\x04"):
                break
        return buf[:-1].decode(errors="replace")

    # ── Public API ──────────────────────────────────────────────────────
    def call(self, rpc_name: str, *params: str) -> str:
        self._connect()
        body = "".join(f"{len(p):05d}{p}" for p in params) if params else ""
        return self._raw(rpc_name, body)

    def close(self):
        if self._sock:
            try:
                self._sock.close()
            finally:
                self._sock = None

    def __enter__(self): return self
    def __exit__(self, *a): self.close()
