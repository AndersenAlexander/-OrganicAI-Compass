# Logging and Redaction

Technical draft — requires legal and operational review before public deployment.

Staging and production logs use JSON records with timestamp, level, service, environment, version, request ID, trace IDs when available, route, method, status, duration and safe error code.

Logs must not include request bodies, response bodies, passwords, tokens, cookies, authorization headers, API keys, email addresses, raw user IDs, message content, transcript content, export contents, uploaded document contents or database URLs.

Task 13A.3 validated sanitized lifecycle and request logging in local staging. Backend startup and shutdown emit JSON lifecycle records for startup completion, shutdown start, provider-client close hook, telemetry flush start/completion, database pool disposal and shutdown completion. Request logs include separate `request_id`, `trace_id` and `span_id` fields without request or response bodies.

Telemetry export failures are logged with a sanitized event name and exception class only. Secret values, provider payloads and personal content are not logged.
