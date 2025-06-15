# Log messages
INJECT_FETCH_ROUTE_CLEANUP = "Cleaning up route interception"
TARGET_CLOSED_ERROR = "Target page/browser/context was closed, skipping interception for {url}"
CONNECTION_CLOSED = "connection was closed"
CONNECTION_NOT_OPEN = "connection was not open"
SYSTEM_PROXY = "SYSTEM_PROXY"

# Handler log messages
HANDLER_WILL_CAPTURE = "Handler {handler_type} will capture: {url}"
HANDLER_REJECTED = "Handler {handler_type} rejected: {url} (content-type: {content_type})"
ALL_HANDLERS_REJECTED = "All handlers rejected: {url}"
HANDLER_CAPTURED_RESPONSE = "Handler {handler_type} captured response from {url} ({current_count}/{max_responses})"
ALL_HANDLERS_COMPLETED = "All handlers reached their max_responses limits, completing..."
TIMEOUT_REACHED = "Timeout reached for multi-handler request to {base_url}. Duration: {duration:.3f}s"

# Cleanup messages
UNROUTE_CLEANUP_ERROR_DIRECT_FETCH = "Error during unroute cleanup in direct_fetch: {error}"

# Text constants
UNLIMITED_SIZE = "unlimited"
UNKNOWN_HEADER_TYPE = "unknown"
NOTHING = "nothing"
