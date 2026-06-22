"""
Cursor pagination engine. ADR-0030 S3.1: cursor-based, no offset.
Uses UUIDv7-compatible ordering (timestamp-prefixed UUID + stable sort).
"""
import base64
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response


class CyberComCursorPagination(CursorPagination):
    """
    Standard cursor pagination for all list endpoints.
    Uses `created_at` as the cursor field for stable ordering.
    Parameters: limit (default 20, max 200), starting_after (cursor).
    """
    page_size = 20
    page_size_query_param = "limit"
    max_page_size = 200
    ordering = "-created_at"
    cursor_query_param = "starting_after"

    def get_paginated_response(self, data):
        return Response({
            "data": data,
            "pagination": {
                "next_cursor": self.get_next_link(),
                "previous_cursor": self.get_previous_link(),
                "has_more": self.get_next_link() is not None,
                "count": len(data),
                "limit": self.page_size,
            },
        })

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "properties": {
                "data": schema,
                "pagination": {
                    "type": "object",
                    "properties": {
                        "next_cursor": {"type": "string", "nullable": True},
                        "previous_cursor": {"type": "string", "nullable": True},
                        "has_more": {"type": "boolean"},
                        "count": {"type": "integer"},
                        "limit": {"type": "integer"},
                    },
                },
            },
        }


class AuditEventCursorPagination(CyberComCursorPagination):
    """Pagination for audit event lists — ordered by timestamp descending."""
    ordering = "-timestamp"
    cursor_query_param = "starting_after"


class ApiUsageCursorPagination(CyberComCursorPagination):
    """Pagination for API usage records."""
    ordering = "-timestamp"
    page_size = 50


class FHIRBundlePagination(CyberComCursorPagination):
    """
    FHIR Bundle pagination. Returns FHIR Bundle format with link relations.
    """
    page_size = 20
    ordering = "-created_at"
    cursor_query_param = "_page_token"

    def get_paginated_response(self, data):
        next_link = self.get_next_link()
        prev_link = self.get_previous_link()

        links = [{"relation": "self", "url": self.request.build_absolute_uri()}]
        if next_link:
            links.append({"relation": "next", "url": next_link})
        if prev_link:
            links.append({"relation": "previous", "url": prev_link})

        return Response({
            "resourceType": "Bundle",
            "type": "searchset",
            "total": len(data),
            "link": links,
            "entry": [{"resource": item} for item in data],
        })
