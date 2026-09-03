"""
Tests for the thin VistaRPC broker client used to talk to Hakeem's MUMPS
backend.

We fake ``socket.create_connection`` with an in-memory socket that records
outgoing bytes and returns canned bytes on ``recv``, so we can assert on the
XWB framing (``[XWB]11302<command><body>\\x04``) without opening a real
connection.
"""
from __future__ import annotations

import pytest


class FakeSocket:
    """Records .sendall() and replays queued .recv() responses (EOT-terminated)."""

    def __init__(self, canned_replies: list[bytes] | None = None):
        self.sent: list[bytes] = []
        self._queue = list(canned_replies or [])
        self.closed = False

    def sendall(self, data: bytes) -> None:
        self.sent.append(data)

    def recv(self, _bufsize: int) -> bytes:
        if not self._queue:
            return b""
        return self._queue.pop(0)

    def close(self) -> None:
        self.closed = True

    def settimeout(self, _t): ...
    def setsockopt(self, *_a, **_kw): ...


def _install_fake_socket(monkeypatch, canned_replies):
    """Patch socket.create_connection inside the mumps_rpc module."""
    from products.cymed.integrations.hakeem import mumps_rpc

    fake = FakeSocket(canned_replies=canned_replies)

    def _create_connection(*_a, **_kw):
        return fake

    monkeypatch.setattr(mumps_rpc.socket, "create_connection", _create_connection)
    return fake


def test_frame_uses_xwb_11302_envelope():
    from products.cymed.integrations.hakeem.mumps_rpc import VistaRpcClient

    framed = VistaRpcClient._frame("ORWPT ID INFO", "some-body")
    assert framed.startswith(b"[XWB]11302")
    assert framed.endswith(b"\x04")  # EOT terminator
    assert b"ORWPT ID INFO" in framed
    assert b"some-body" in framed


def test_frame_with_empty_body_still_terminates_with_eot():
    from products.cymed.integrations.hakeem.mumps_rpc import VistaRpcClient

    framed = VistaRpcClient._frame("XUS SIGNON SETUP")
    assert framed == b"[XWB]11302XUS SIGNON SETUP\x04"


def test_call_sends_length_prefixed_params_and_returns_payload(monkeypatch):
    """
    On .call('ORWPT ID INFO', '1112223334') we expect:
      * a live TCP connection attempt (patched to our FakeSocket),
      * 3 login frames (XWB CREATE CONTEXT, XUS SIGNON SETUP, XUS AV CODE),
      * then the RPC frame with the param length-prefixed as '10' + value,
      * and .call() returns the decoded payload with the trailing \\x04 stripped.
    """
    from products.cymed.integrations.hakeem.mumps_rpc import VistaRpcClient

    # 4 replies: 3 for login handshake + 1 for the actual RPC.
    replies = [
        b"OK\x04",
        b"OK\x04",
        b"OK\x04",
        b"NAME^19800101^M^1112223334\x04",
    ]
    fake = _install_fake_socket(monkeypatch, replies)

    client = VistaRpcClient(host="127.0.0.1", port=9999,
                              access="ACCESS", verify="VERIFY")
    payload = client.call("ORWPT ID INFO", "1112223334")

    # No trailing EOT in return value
    assert payload == "NAME^19800101^M^1112223334"

    # 4 frames sent: 3 login + 1 RPC
    assert len(fake.sent) == 4
    login_frames = fake.sent[:3]
    rpc_frame = fake.sent[3]

    assert b"XWB CREATE CONTEXT" in login_frames[0]
    assert b"XUS SIGNON SETUP" in login_frames[1]
    assert b"XUS AV CODE" in login_frames[2]
    assert b"ACCESS;VERIFY" in login_frames[2]

    # RPC frame: [XWB]11302ORWPT ID INFO00010<param>\x04
    assert rpc_frame.startswith(b"[XWB]11302ORWPT ID INFO")
    assert b"000101112223334" in rpc_frame  # length "00010" + 10-char id
    assert rpc_frame.endswith(b"\x04")


def test_close_returns_socket_to_disconnected_state(monkeypatch):
    from products.cymed.integrations.hakeem.mumps_rpc import VistaRpcClient

    fake = _install_fake_socket(monkeypatch, [b"OK\x04", b"OK\x04", b"OK\x04"])
    client = VistaRpcClient(host="127.0.0.1", port=9999,
                              access="A", verify="B")
    client._connect()
    assert client._sock is fake

    client.close()
    assert client._sock is None
    assert fake.closed is True


def test_context_manager_closes_socket(monkeypatch):
    from products.cymed.integrations.hakeem.mumps_rpc import VistaRpcClient

    fake = _install_fake_socket(
        monkeypatch,
        [b"OK\x04", b"OK\x04", b"OK\x04", b"row1^a\nrow2^b\x04"],
    )

    with VistaRpcClient(host="127.0.0.1", port=9999,
                         access="A", verify="B") as rpc:
        payload = rpc.call("ORWPS ACTIVE", "1112223334")

    assert payload == "row1^a\nrow2^b"
    assert fake.closed is True
