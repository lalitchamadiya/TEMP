import re
from django.core.exceptions import ValidationError

def normalize_phone_number(phone_str, default_prefix='+91'):
    r"""
    Normalizes a given phone number string into international format (e.g. +919327431562).
    - If empty/None, returns empty string.
    - Strips spaces, dashes, parentheses, and dots.
    - If 10 digits (e.g. '9327431562'), prepends default_prefix (+91).
    - If starts with leading zero (e.g. '09327431562'), removes 0 and prepends default_prefix.
    - If 12 digits starting with '91' without '+' (e.g. '919327431562'), prepends '+'.
    - If already starts with '+', preserves international format.
    - Validates international format ^\+\d{7,15}$
    """
    if not phone_str:
        return ''

    # Clean whitespace, hyphens, brackets, dots
    cleaned = re.sub(r'[\s\-\(\)\.]', '', str(phone_str))
    
    if not cleaned:
        return ''

    # Case 1: Starts with +
    if cleaned.startswith('+'):
        normalized = cleaned
    # Case 2: Starts with 0 (e.g. 09327431562)
    elif cleaned.startswith('0'):
        cleaned_no_zero = cleaned.lstrip('0')
        normalized = f"{default_prefix}{cleaned_no_zero}"
    # Case 3: 12 digits starting with 91 (e.g. 919327431562)
    elif len(cleaned) == 12 and cleaned.startswith('91'):
        normalized = f"+{cleaned}"
    # Case 4: 10 digits (standard Indian mobile number, e.g. 9327431562)
    elif len(cleaned) == 10 and cleaned.isdigit():
        normalized = f"{default_prefix}{cleaned}"
    # Case 5: Any other number without +, check if digits only
    elif cleaned.isdigit():
        normalized = f"{default_prefix}{cleaned}"
    else:
        normalized = cleaned

    # Validation check: international format with 10 to 15 digits after +
    pattern = r'^\+\d{10,15}$'
    if not re.match(pattern, normalized):
        raise ValidationError(
            f"Enter a valid phone number in international format e.g. +919327431562"
        )

    return normalized


import base64
import mimetypes

def file_to_base64(uploaded_file):
    """
    Converts a Django UploadedFile to a Base64 Data URI string.
    Returns string in format: 'data:image/png;base64,iVBORw0KGgo...'
    """
    if not uploaded_file:
        return None
    try:
        uploaded_file.seek(0)
        content = uploaded_file.read()
        uploaded_file.seek(0)
        
        mime_type, _ = mimetypes.guess_type(uploaded_file.name)
        if not mime_type or not mime_type.startswith('image/'):
            mime_type = 'image/jpeg'
            
        b64_str = base64.b64encode(content).decode('utf-8')
        return f"data:{mime_type};base64,{b64_str}"
    except Exception as e:
        print(f"Error encoding file to Base64: {e}")
        return None

