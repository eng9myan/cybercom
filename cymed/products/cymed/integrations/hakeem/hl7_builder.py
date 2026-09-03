"""HL7 v2.5 message builders for Hakeem push messages."""
from datetime import datetime


def _seg(*fields: str) -> str:
    return "|".join(fields)


def _now() -> str:
    return datetime.utcnow().strftime("%Y%m%d%H%M%S")


def build_oru_r01(*, patient_national_id: str, patient_name: str,
                  observations: list[dict], sending_facility: str = "CYMED",
                  receiving_facility: str = "HAKEEM") -> str:
    """
    Construct an ORU^R01 message for laboratory or observation results.
    observations = [{code, name, value, units, ref_range, flag, timestamp}]
    """
    msg_id = _now() + "-" + patient_national_id[-4:]
    msh = _seg("MSH", "^~\\&", "CYMED", sending_facility, "HAKEEM",
                receiving_facility, _now(), "", "ORU^R01^ORU_R01", msg_id,
                "P", "2.5")
    pid = _seg("PID", "1", "", patient_national_id, "",
                patient_name.replace(" ", "^"), "", "", "", "", "", "", "")
    obr = _seg("OBR", "1", msg_id, msg_id, "^^^LAB", "", "", _now())
    obx_lines = []
    for i, o in enumerate(observations, start=1):
        obx_lines.append(_seg(
            "OBX", str(i), "NM",
            f"{o.get('code','')}^{o.get('name','')}^L",
            "", str(o.get("value", "")),
            o.get("units", ""), o.get("ref_range", ""),
            o.get("flag", "N"), "", "", "F",
            "", o.get("timestamp", _now()),
        ))
    return "\r".join([msh, pid, obr, *obx_lines])


def build_mdm_t02(*, patient_national_id: str, patient_name: str,
                  document_type: str, document_text: str,
                  sending_facility: str = "CYMED",
                  receiving_facility: str = "HAKEEM") -> str:
    """Discharge / encounter summary."""
    msg_id = _now() + "-" + patient_national_id[-4:]
    msh = _seg("MSH", "^~\\&", "CYMED", sending_facility, "HAKEEM",
                receiving_facility, _now(), "", "MDM^T02^MDM_T02", msg_id,
                "P", "2.5")
    evn = _seg("EVN", "T02", _now())
    pid = _seg("PID", "1", "", patient_national_id, "",
                patient_name.replace(" ", "^"))
    txa = _seg("TXA", "1", document_type, "TX", _now(), "", "", "", "", "", "",
                msg_id, "", "", "AV", "", "F")
    obx_body = _seg("OBX", "1", "TX", document_type, "", document_text.replace("\n", "\\.br\\"))
    return "\r".join([msh, evn, pid, txa, obx_body])
