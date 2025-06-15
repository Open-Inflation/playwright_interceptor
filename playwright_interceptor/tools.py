from beartype import beartype


@beartype
def parse_content_type(content_type: str) -> dict[str, str]:
    """
    Parses Content-Type string and returns dictionary with main type and parameters.
    
    Args:
        content_type: Content-Type from response headers (e.g., "text/html; charset=utf-8")
    
    Returns:
        Dictionary with 'content_type' key for main type and all additional parameters
    """
    if not content_type:
        return {'content_type': '', 'charset': 'utf-8'}
    
    # Split string into parts and remove extra spaces
    parts = [p.strip() for p in content_type.split(';')]

    # Main content type always in lowercase
    result = {
        'content_type': parts[0].lower(),
        'charset': 'utf-8'  # Set utf-8 as default
    }

    # Process additional parameters
    for part in parts[1:]:
        if not part:
            continue

        if '=' in part:
            key, value = part.split('=', 1)
            key = key.strip().lower()
            # Remove quotes if present
            value = value.strip().strip('"\'')
            if key == 'charset':
                value = value.lower()
                result['charset'] = value
            else:
                result[key] = value
        else:
            # For parameters without values
            result[part.lower()] = ''
    
    return result

