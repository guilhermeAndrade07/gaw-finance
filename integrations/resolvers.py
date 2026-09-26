import unicodedata

from categories.models import Category
from banks.models import Bank


def _normalize(text):
    normalized = unicodedata.normalize('NFKD', str(text))
    return ''.join(c for c in normalized if not unicodedata.combining(c)).lower().strip()


def _match(query, name):
    clean_query = _normalize(query)
    clean_name = _normalize(name)
    if not clean_query:
        return False
    return clean_query in clean_name or _token_match(clean_query, clean_name)


def _token_match(query, name):
    query_tokens = query.split()
    name_tokens = name.split()
    for q in query_tokens:
        if len(q) < 3:
            continue
        for n in name_tokens:
            if n.startswith(q) or q.startswith(n):
                return True
    return False


def _find_first(user, queryset, name):
    candidates = list(queryset)
    for item in candidates:
        if _match(name, item.name):
            return item
    return None


def resolve_bank(user, name):
    if not name:
        return None
    return _find_first(user, Bank.objects.filter(user=user), name)


def resolve_category(user, name):
    if not name:
        return None
    return _find_first(user, Category.objects.filter(user=user), name)
