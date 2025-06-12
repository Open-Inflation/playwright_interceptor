# Timeout constants
MAX_TIMEOUT_SECONDS = 3600  # 1 час максимум
MILLISECONDS_MULTIPLIER = 1000  # Конвертация секунд в миллисекунды
LOG_FORMAT = '[%(asctime)s] %(levelname)s %(name)s: %(message)s'

# JavaScript file name
INJECT_FETCH_JS_FILE = "inject_fetch.js"

# Default values
DEFAULT_CONTENT_TYPE = "application/json"

# Неподдерживаемые протоколы для Route.fetch()
UNSUPPORTED_PROTOCOLS = (
    'chrome-extension:',
    'moz-extension:',
    'ms-browser-extension:',
    'safari-web-extension:',
    'edge-extension:',
)
