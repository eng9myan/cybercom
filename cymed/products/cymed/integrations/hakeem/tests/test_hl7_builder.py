"""
Tests for HL7 v2.5 message builders used to push data to Hakeem.

``build_oru_r01`` must produce a message with MSH, PID, OBR and OBX segments;
``build_mdm_t02`` must produce a message with EVN and TXA segments (in addition
to MSH/PID).
"""
from __future__ import annotations

import pytest


def _segments(msg: str) -> list[list[str]]:
    """Split an HL7 v2 message on CR and each segment on the field separator."""
    return [seg.split("|") for seg in msg.split("\r") if seg]


def _segment_ids(msg: str) -> list[str]:
    return [seg[0] for seg in _segments(msg)]


def test_build_oru_r01_has_msh_pid_obr_obx_segments():
    from products.cymed.integrations.hakeem.hl7_builder import build_oru_r01

    observations = [
        {"code": "718-7", "name": "Hemoglobin", "value": "13.4",
         "units": "g/dL", "ref_range": "12-17", "flag": "N"},
        {"code": "2093-3", "name": "Cholesterol", "value": "210",
         "units": "mg/dL", "ref_range": "<200", "flag": "H"},
    ]

    msg = build_oru_r01(
        patient_national_id="1112223334",
        patient_name="Ali Al Zahrani",
        observations=observations,
    )

    ids = _segment_ids(msg)
    assert ids[0] == "MSH"
    assert "PID" in ids
    assert "OBR" in ids
    assert ids.count("OBX") == len(observations)

    msh = _segments(msg)[0]
    # MSH-9 = message type ORU^R01^ORU_R01 (index 8 because MSH-1 is separators)
    assert "ORU^R01" in msh[8]
    assert "2.5" in msh[11]

    pid = next(s for s in _segments(msg) if s[0] == "PID")
    assert pid[3] == "1112223334"
    assert "Ali^Al^Zahrani" in pid[5]


def test_build_oru_r01_encodes_each_observation_in_own_obx_segment():
    from products.cymed.integrations.hakeem.hl7_builder import build_oru_r01

    observations = [
        {"code": "L1", "name": "Test1", "value": "1", "units": "u",
         "ref_range": "0-2", "flag": "N"},
        {"code": "L2", "name": "Test2", "value": "9", "units": "u",
         "ref_range": "0-2", "flag": "H"},
        {"code": "L3", "name": "Test3", "value": "3", "units": "u",
         "ref_range": "0-2", "flag": "H"},
    ]
    msg = build_oru_r01(patient_national_id="1234567890",
                         patient_name="Test Patient",
                         observations=observations)
    obx_segments = [s for s in _segments(msg) if s[0] == "OBX"]
    assert len(obx_segments) == 3
    # Sequence numbers 1..N in OBX-1
    assert [s[1] for s in obx_segments] == ["1", "2", "3"]
    # Value in OBX-5
    assert [s[5] for s in obx_segments] == ["1", "9", "3"]


def test_build_mdm_t02_has_evn_and_txa_segments():
    from products.cymed.integrations.hakeem.hl7_builder import build_mdm_t02

    msg = build_mdm_t02(
        patient_national_id="1112223334",
        patient_name="Ali Al Zahrani",
        document_type="Discharge Summary",
        document_text="Patient discharged in stable condition.",
    )

    ids = _segment_ids(msg)
    assert ids[0] == "MSH"
    assert "EVN" in ids
    assert "PID" in ids
    assert "TXA" in ids

    msh = _segments(msg)[0]
    assert "MDM^T02" in msh[8]

    evn = next(s for s in _segments(msg) if s[0] == "EVN")
    assert evn[1] == "T02"
    assert evn[2] and evn[2].isdigit()  # timestamp

    txa = next(s for s in _segments(msg) if s[0] == "TXA")
    assert txa[2] == "Discharge Summary"
    assert txa[3] == "TX"


def test_build_mdm_t02_escapes_newlines_in_body():
    from products.cymed.integrations.hakeem.hl7_builder import build_mdm_t02

    msg = build_mdm_t02(
        patient_national_id="1112223334",
        patient_name="Ali Al Zahrani",
        document_type="Discharge Summary",
        document_text="line1\nline2\nline3",
    )
    # Raw newlines must be encoded as \.br\ so the payload stays a single HL7
    # segment.
    obx = next(s for s in _segments(msg) if s[0] == "OBX")
    assert "\n" not in obx[5]
    assert obx[5].count("\\.br\\") == 2
