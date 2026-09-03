"""Bundle transaction executor.

Iterates entries in a FHIR Bundle (type=transaction|batch), routes each entry
to the appropriate mapper, aggregates responses into a response Bundle.
"""
from django.db import transaction

from .registry import get_mapper


def execute_bundle(bundle: dict) -> dict:
    bundle_type = bundle.get("type", "batch")
    entries = bundle.get("entry", [])
    responses = []

    if bundle_type == "transaction":
        with transaction.atomic():
            for e in entries:
                responses.append(_execute_entry(e))
    else:
        for e in entries:
            try:
                responses.append(_execute_entry(e))
            except Exception as exc:  # noqa: BLE001
                responses.append({"response": {"status": f"500 {exc}"}})

    return {
        "resourceType": "Bundle",
        "type": f"{bundle_type}-response",
        "entry": responses,
    }


def _execute_entry(entry: dict) -> dict:
    req = entry.get("request", {})
    method = req.get("method", "GET").upper()
    url = req.get("url", "")
    resource_type = url.split("/", 1)[0] if url else entry.get("resource", {}).get("resourceType")
    mapper = get_mapper(resource_type)

    if method == "POST":
        obj = mapper.from_fhir(entry.get("resource", {}))
        obj.save()
        return {"response": {"status": "201 Created", "location": f"{resource_type}/{obj.id}"},
                "resource": mapper.to_fhir(obj)}
    if method == "PUT":
        # naive update: expect id in URL Resource/{id}
        _, id_ = url.split("/", 1)
        model = mapper.django_model
        obj = model.objects.get(id=id_)
        payload = entry.get("resource", {})
        new = mapper.from_fhir(payload)
        for f in obj._meta.fields:
            if f.name in ("id", "created_at"): continue
            v = getattr(new, f.name, None)
            if v is not None: setattr(obj, f.name, v)
        obj.save()
        return {"response": {"status": "200 OK"}, "resource": mapper.to_fhir(obj)}
    if method == "GET":
        parts = url.split("?", 1)
        path = parts[0]
        params = dict(kv.split("=", 1) for kv in parts[1].split("&")) if len(parts) == 2 else {}
        if "/" in path:
            _, id_ = path.split("/", 1)
            obj = mapper.django_model.objects.get(id=id_)
            return {"response": {"status": "200 OK"}, "resource": mapper.to_fhir(obj)}
        qs = mapper.search(params)
        return {"response": {"status": "200 OK"},
                "resource": {"resourceType": "Bundle", "type": "searchset",
                              "entry": [{"resource": mapper.to_fhir(o)} for o in qs]}}
    return {"response": {"status": f"501 Not Implemented for {method}"}}
