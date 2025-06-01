# http(s)://user:pass@host:port
PROXY = r'^(?:(?P<scheme>https?:\/\/))?(?:(?P<username>[^:@]+):(?P<password>[^@]+)@)?(?P<host>[^:\/]+)(?::(?P<port>\d+))?$'

# Timeout constants
MAX_TIMEOUT_SECONDS = 3600  # 1 час максимум
MILLISECONDS_MULTIPLIER = 1000  # Конвертация секунд в миллисекунды

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
LOG_REQUEST_MODIFIER_FAILED_TYPE = "request_modifier_func returned non-Request object"
LOG_REQUEST_MODIFIER_ANY_TYPE = "Request method ANY - is not a specific type."
LOG_PAGE_NOT_AVAILABLE = "Page is not available"
LOG_FAILED_TO_GET_RESPONSE_BODY = "Failed to get response body for"

# File extensions mapping
IMAGE_EXTENSIONS = {
    'image/jpeg': '.jpg',
    'image/jpg': '.jpg', 
    'image/png': '.png',
    'image/gif': '.gif',
    'image/webp': '.webp',
    'image/svg+xml': '.svg',
    'image/x-icon': '.ico',
    'image/vnd.microsoft.icon': '.ico',
    'image/bmp': '.bmp',
    'image/x-ms-bmp': '.bmp',
    'image/tiff': '.tiff',
}

VIDEO_EXTENSIONS = {
    'video/mp4': '.mp4',
    'video/webm': '.webm',
    'video/ogg': '.ogv',
    'video/avi': '.avi',
    'video/x-msvideo': '.avi',
    'video/quicktime': '.mov',
    'video/x-ms-wmv': '.wmv',
    'video/x-flv': '.flv',
    'video/3gpp': '.3gp',
    'video/x-matroska': '.mkv',
}

AUDIO_EXTENSIONS = {
    'audio/mpeg': '.mp3',
    'audio/mp3': '.mp3',
    'audio/wav': '.wav',
    'audio/x-wav': '.wav',
    'audio/ogg': '.ogg',
    'audio/flac': '.flac',
    'audio/aac': '.aac',
    'audio/x-ms-wma': '.wma',
    'audio/mp4': '.m4a',
    'audio/webm': '.weba',
}

FONT_EXTENSIONS = {
    'font/ttf': '.ttf',
    'font/otf': '.otf',
    'font/woff': '.woff',
    'font/woff2': '.woff2',
    'application/font-woff': '.woff',
    'application/font-woff2': '.woff2',
    'application/x-font-ttf': '.ttf',
    'application/x-font-otf': '.otf',
    'application/vnd.ms-fontobject': '.eot',
}

APPLICATION_EXTENSIONS = {
    'application/pdf': '.pdf',
    'application/vnd.ms-excel': '.xls',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
    'application/msword': '.doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'application/vnd.ms-powerpoint': '.ppt',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
    'application/octet-stream': '.bin',
    'application/x-executable': '.exe',
    'application/x-sharedlib': '.so',
    'application/x-library': '.lib',
}

ARCHIVE_EXTENSIONS = {
    'application/zip': '.zip',
    'application/x-rar-compressed': '.rar',
    'application/x-7z-compressed': '.7z',
    'application/x-tar': '.tar',
    'application/gzip': '.gz',
    'application/x-bzip2': '.bz2',
    'application/x-xz': '.xz',
    'application/x-lzma': '.lzma',
    'application/x-compress': '.Z',
    'application/x-cab': '.cab',
}

TEXT_EXTENSIONS = {
    'text/plain': '.txt',
    'text/csv': '.csv',
    'text/xml': '.xml',
    'text/markdown': '.md',
    'text/rtf': '.rtf',
    'application/xml': '.xml',
    'application/rss+xml': '.rss',
    'application/atom+xml': '.atom',
}

# JSON extensions (отдельно, так как это самостоятельный формат)
JSON_EXTENSIONS = {
    'application/json': '.json',
    'application/ld+json': '.jsonld',
    'application/json-patch+json': '.json-patch',
}

JS_EXTENSIONS = {
    'application/javascript': '.js',
    'text/javascript': '.js',
    'application/x-javascript': '.js',
}

CSS_EXTENSIONS = {
    'text/css': '.css',
    'application/css': '.css',
    'application/x-css': '.css',
}

# Archive MIME types (для проверки архивов)
ARCHIVE_MIME_TYPES = [
    'application/zip',
    'application/gzip', 
    'application/x-rar-compressed',
    'application/x-7z-compressed',
    'application/x-tar',
    'application/x-bzip2',
    'application/x-xz',
    'application/x-lzma',
    'application/x-compress',
    'application/x-cab',
]

# Default file extensions
DEFAULT_IMAGE_EXTENSION = '.img'
DEFAULT_IMAGE_NAME = "image"

# Proxy constants
PROXY_HTTP_SCHEMES = ['http://', 'https://']
