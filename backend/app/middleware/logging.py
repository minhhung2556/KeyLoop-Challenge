import time
import json
import logging
from typing import Callable, Set
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Message

logger = logging.getLogger(__name__)

SENSITIVE_FIELDS: Set[str] = {
    "password",
    "token",
    "idToken",
    "id_token",
    "refreshToken",
    "refresh_token",
    "apiKey",
    "api_key",
    "secret",
    "private_key",
    "authorization",
    "customToken",
    "custom_token",
    "oobCode",
    "oob_code",
    "checksum_key",
    "signature",
}

PII_FIELDS: Set[str] = {
    "email",
    "localId",
    "local_id",
    "passwordHash",
    "password_hash",
    "federatedId",
    "federated_id",
    "rawId",
    "raw_id",
    "displayName",
    "display_name",
    "phoneNumber",
    "phone_number",
    "providerUserInfo",
    "provider_user_info",
    "lastLoginAt",
    "last_login_at",
    "createdAt",
    "created_at",
    "passwordUpdatedAt",
    "password_updated_at",
    "validSince",
    "valid_since",
    "lastRefreshAt",
    "last_refresh_at",
}

MASKED_LOG_FIELDS: Set[str] = SENSITIVE_FIELDS | PII_FIELDS

SENSITIVE_HEADERS: Set[str] = {
    "authorization",
    "cookie",
    "x-api-key",
}


def _field_matches_key(field: str, key_lower: str) -> bool:
    normalized_field = field.replace("_", "").lower()
    normalized_key = key_lower.replace("_", "")
    return normalized_field in normalized_key or field in key_lower


def mask_sensitive_data(data: dict, fields: Set[str] = MASKED_LOG_FIELDS) -> dict:
    if not isinstance(data, dict):
        return data
    masked = {}
    for key, value in data.items():
        key_lower = key.lower()
        if any(_field_matches_key(field, key_lower) for field in fields):
            masked[key] = "***"
        elif isinstance(value, dict):
            masked[key] = mask_sensitive_data(value, fields)
        elif isinstance(value, list):
            masked[key] = [
                mask_sensitive_data(item, fields) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            masked[key] = value
    return masked


def truncate_body(body: str, max_length: int) -> str:
    if len(body) <= max_length:
        return body
    return body[:max_length] + f"... [truncated, total {len(body)} chars]"


def sanitize_headers(headers: dict) -> dict:
    sanitized = {}
    for key, value in headers.items():
        if key.lower() in SENSITIVE_HEADERS:
            sanitized[key] = "***"
        else:
            sanitized[key] = value
    return sanitized


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        log_request_body: bool = True,
        log_response_body: bool = True,
        max_body_length: int = 10000,
        exclude_paths: Set[str] = None,
    ):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_length = max_body_length
        self.exclude_paths = exclude_paths or {"/health", "/", "/favicon.ico"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        request_id = getattr(request.state, "request_id", "-")
        start_time = time.time()

        method = request.method
        path = request.url.path
        query = str(request.query_params) if request.query_params else ""

        logger.debug(
            f"[{request_id}] --> {method} {path}" + (f"?{query}" if query else "")
        )

        if self.log_request_body and method in ("POST", "PUT", "PATCH"):
            await self._log_request_body(request, request_id)

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000
        status_code = response.status_code

        log_method = logger.debug if status_code < 400 else logger.warning
        if status_code >= 500:
            log_method = logger.error

        log_method(
            f"[{request_id}] <-- {method} {path} {status_code} ({duration_ms:.1f}ms)"
        )

        if self.log_response_body:
            response = await self._log_response_body(response, request_id)

        return response

    async def _log_request_body(self, request: Request, request_id: str):
        try:
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                body = await request.body()
                if body:
                    try:
                        body_json = json.loads(body)
                        masked = mask_sensitive_data(body_json)
                        body_str = json.dumps(masked)
                        body_str = truncate_body(body_str, self.max_body_length)
                        logger.debug(f"[{request_id}] Request Body: {body_str}")
                    except json.JSONDecodeError:
                        logger.debug(
                            f"[{request_id}] Request Body: [non-JSON, {len(body)} bytes]"
                        )
            elif "multipart/form-data" in content_type:
                logger.debug(f"[{request_id}] Request Body: [multipart form data]")
        except Exception as e:
            logger.debug(f"[{request_id}] Could not read request body: {e}")

    async def _log_response_body(
        self, response: Response, request_id: str
    ) -> Response:
        try:
            body_parts = []
            async for chunk in response.body_iterator:
                body_parts.append(chunk)

            body = b"".join(body_parts)

            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type and body:
                try:
                    body_json = json.loads(body)
                    masked = mask_sensitive_data(body_json)
                    body_str = json.dumps(masked)
                    body_str = truncate_body(body_str, self.max_body_length)
                    logger.debug(f"[{request_id}] Response Body: {body_str}")
                except json.JSONDecodeError:
                    logger.debug(
                        f"[{request_id}] Response Body: [non-JSON, {len(body)} bytes]"
                    )

            async def body_iterator():
                yield body

            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        except Exception as e:
            logger.debug(f"[{request_id}] Could not read response body: {e}")
            return response
