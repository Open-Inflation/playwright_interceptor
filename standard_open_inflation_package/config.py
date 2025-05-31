
# http(s)://user:pass@host:port
PROXY = r'^(?:(?P<scheme>https?:\/\/))?(?:(?P<username>[^:@]+):(?P<password>[^@]+)@)?(?P<host>[^:\/]+)(?::(?P<port>\d+))?$'

# Timeout constants
MAX_TIMEOUT_SECONDS = 3600  # 1 час максимум
MILLISECONDS_MULTIPLIER = 1000  # Конвертация секунд в миллисекунды

# Content-Type constants
CONTENT_TYPE_JSON = "application/json"
CONTENT_TYPE_HTML = "text/html"
CONTENT_TYPE_IMAGE = "image/"
CONTENT_TYPE_JAVASCRIPT = "javascript"
CONTENT_TYPE_CSS = "text/css"

# JavaScript file name
INJECT_FETCH_JS_FILE = "inject_fetch.js"

# Default values
DEFAULT_CONTENT_TYPE = "application/json"
DEFAULT_HTTP_SCHEME = "http://"
DEFAULT_COOKIE_PATH = "/"

# Error messages
ERROR_UNKNOWN = "UnknownError"
ERROR_MESSAGE_UNKNOWN = "Unknown error occurred"
ERROR_TIMEOUT_POSITIVE = "Timeout must be positive"
ERROR_TIMEOUT_TOO_LARGE = "Timeout too large (max 3600 seconds)"
ERROR_UNKNOWN_CONNECTION_TYPE = "Unknown connection type"
ERROR_JS_FILE_NOT_FOUND = "JavaScript file not found at"

# Log messages
LOG_NEW_PAGE_CREATING = "Creating a new page in the browser context..."
LOG_NEW_PAGE_CREATED = "New page created successfully."
LOG_BROWSER_CONTEXT_OPENED = "A new browser context has been opened."
LOG_START_FUNC_EXECUTING = "Executing start function"
LOG_START_FUNC_EXECUTED = "executed successfully."
LOG_NEW_SESSION_CREATED = "New session created successfully."
LOG_REQUEST_COMPLETED = "Request completed in"
LOG_INJECT_FETCH_COMPLETED = "Inject fetch request completed in"
LOG_PAGE_CLOSED = "Page closed successfully"
LOG_NO_PAGE_TO_CLOSE = "No page to close"
LOG_CLOSING_CONNECTION = "Closing"
LOG_CONNECTION_CLOSED = "connection was closed"
LOG_CONNECTION_NOT_OPEN = "connection was not open"
LOG_PREPARING_TO_CLOSE = "Preparing to close"
LOG_NO_CONNECTIONS = "No connections to close"
LOG_ERROR_CLOSING = "Error closing"
LOG_OPENING_BROWSER = "Opening new browser connection with proxy"
LOG_SYSTEM_PROXY = "SYSTEM_PROXY"
LOG_PROCESSING_COOKIE = "Processing Set-Cookie header"
LOG_COOKIE_SET = "Cookie set"
LOG_COOKIE_PROCESSING_FAILED = "Failed to process Set-Cookie header"
LOG_CUSTOM_HEADERS_WARNING = "Custom headers generator returned non-dict"

# File extensions mapping
IMAGE_EXTENSIONS = {
    'image/jpeg': '.jpg',
    'image/jpg': '.jpg', 
    'image/png': '.png',
    'image/gif': '.gif',
    'image/webp': '.webp',
    'image/svg+xml': '.svg'
}

# Default file extensions
DEFAULT_IMAGE_EXTENSION = '.img'
DEFAULT_IMAGE_NAME = "image"

# Proxy constants
PROXY_HTTP_SCHEMES = ['http://', 'https://']
