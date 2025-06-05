# Log messages
NEW_PAGE_CREATING = "Creating a new page in the browser context..."
NEW_PAGE_CREATED = "New page created successfully."
BROWSER_CONTEXT_OPENED = "A new browser context has been opened."
START_FUNC_EXECUTING = "Executing start function: {function_name}"
START_FUNC_EXECUTED  = "Executing start function {function_name} executed successfully."
NEW_SESSION_CREATED = "New session created successfully."
INJECT_FETCH_COMPLETED = "Inject fetch request completed in {duration:.3f}s"
PAGE_CLOSED = "Page closed successfully"
CLOSING_CONNECTION = "Closing {connection_name} connection..."
CONNECTION_CLOSED = "connection was closed"
CONNECTION_NOT_OPEN = "connection was not open"
PREPARING_TO_CLOSE = "Preparing to close: {connections}"
NO_CONNECTIONS = "No connections to close"
OPENING_BROWSER = "Opening new browser connection with proxy: {proxy}"
SYSTEM_PROXY = "SYSTEM_PROXY"
REQUEST_MODIFIER_FAILED_TYPE = "request_modifier_func returned non-Request object: {object_type}"
REQUEST_MODIFIER_ANY_TYPE = "Request method ANY - is not a specific type."
PAGE_NOT_AVAILABLE = "Page is not available"

# Handler log messages
HANDLER_WILL_CAPTURE = "Handler {handler_type} will capture: {url}"
HANDLER_REJECTED = "Handler {handler_type} rejected: {url} (content-type: {content_type})"
ALL_HANDLERS_REJECTED = "All handlers rejected: {url}"
HANDLER_CAPTURED_RESPONSE = "Handler {handler_type} captured response from {url} ({current_count}/{max_responses})"
ALL_HANDLERS_COMPLETED = "All handlers reached their max_responses limits, completing..."
TIMEOUT_REACHED = "Timeout reached for multi-handler request to {base_url}. Duration: {duration:.3f}s"

# Proxy log messages
PARSING_PROXY = "Parsing proxy string: {proxy_string}"
PROXY_NOT_PROVIDED = "Proxy string not provided, checking environment variables for HTTP(S)_PROXY"
NO_PROXY_FOUND = "No proxy string found, returning None"
PROXY_FOUND_IN_ENV = "Proxy string found in environment variables"
PROXY_PARSED_BASIC = "Proxy parsed as basic"
PROXY_WITH_CREDENTIALS = "Proxy WITH credentials"
PROXY_WITHOUT_CREDENTIALS = "Proxy WITHOUT credentials"
PROXY_PARSED_REGEX = "Proxy parsed as regex"

# Connection log messages
CONNECTION_CLOSED_SUCCESS = "The {connection_name} {status}"
CONNECTION_NOT_OPEN_WARNING = "The {connection_name} {status}"

# Cookie management messages
COOKIE_ADDED = "Cookie added: {name}={value} for domain {domain}"
COOKIES_ADDED = "Added {count} cookies"
COOKIE_REMOVED = "Cookie removed: {name}"
COOKIES_REMOVED = "Removed {count} cookies"
COOKIE_NOT_FOUND = "Cookie '{name}' not found for removal"

# Text constants
UNLIMITED_SIZE = "unlimited"
UNKNOWN_HEADER_TYPE = "unknown"
NOTHING = "nothing"
