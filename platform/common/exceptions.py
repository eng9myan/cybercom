"""
Standardized exception classes for CyberCom platform. ADR-0003 (API strategy).
All exceptions serialize to RFC 7807 Problem Detail format.
"""
from rest_framework.exceptions import APIException
from rest_framework import status


class CyberComAPIException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "An unexpected platform error occurred."
    default_code = "platform_error"


class TenantNotFound(CyberComAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Tenant not found or inactive."
    default_code = "tenant_not_found"


class TenantMissing(CyberComAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Tenant context is required for this operation."
    default_code = "tenant_missing"


class AuthenticationRequired(CyberComAPIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Authentication credentials were not provided or are invalid."
    default_code = "authentication_required"


class InsufficientPermissions(CyberComAPIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You do not have permission to perform this action."
    default_code = "insufficient_permissions"


class ResourceNotFound(CyberComAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "The requested resource was not found."
    default_code = "resource_not_found"


class ConflictError(CyberComAPIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "A conflict occurred with the current resource state."
    default_code = "conflict"


class ValidationError(CyberComAPIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Validation failed."
    default_code = "validation_error"
