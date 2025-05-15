import re


def is_git_url(source: str) -> bool:
    """Проверяет, является ли строка Git URL"""
    pattern = r'^https://.+\.git$'
    return re.match(pattern, source, re.IGNORECASE) is not None
