# http(s)://user:pass@host:port
PROXY = r'^(?:(?P<scheme>https?:\/\/))?(?:(?P<username>[^:@]+):(?P<password>[^@]+)@)?(?P<host>[^:\/]+)(?::(?P<port>\d+))?$'

# Proxy constants
PROXY_HTTP_SCHEMES = ['http://', 'https://']
DEFAULT_HTTP_SCHEME = PROXY_HTTP_SCHEMES[0]

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
    'text/html': '.html',
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
