from .parameters import MAX_TIMEOUT_SECONDS

# Error messages
UNKNOWN = "UnknownError"
MESSAGE_UNKNOWN = "Unknown error occurred"
TIMEOUT_POSITIVE = "Timeout must be positive"
TIMEOUT_TOO_LARGE = f"Timeout too large (max {MAX_TIMEOUT_SECONDS} seconds)"
UNKNOWN_CONNECTION_TYPE = "Unknown connection type"
JS_FILE_NOT_FOUND = "JavaScript file not found at"
DUPLICATE_HANDLER_SLUGS = "Duplicate handler slugs detected: {duplicate_slugs}"
UNKNOWN_HANDLER_TYPE = "Unknown handler type: {handler_type}"
BROWSER_COMPONENT_CLOSING = "Error closing"
FAILED_PROCESS_RESPONSE = "Failed to process response for handlers {handler_list} from {url}: {error}"
PROXY_PATTERN_MISMATCH = "Proxy string did not match expected pattern, using basic formating"
PROXY_MISSING_PROTOCOL = "Proxy string missing protocol, prepending 'http://'"
NO_PAGE_TO_CLOSE = "No page to close"
