import re
import unicodedata


def slugify(value: str) -> str:
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^a-zA-Z0-9\s-]', '', value).strip().lower()
    value = re.sub(r'[-\s]+', '-', value)
    return value or 'project'
