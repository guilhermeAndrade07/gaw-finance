from categories.models import Category


DEFAULT_CATEGORY_NAMES = [
    'Transporte',
    'Mercado',
    'Saúde',
    'Educação',
    'Lazer',
    'Assinatura',
]


def create_default_categories(user):
    """Creates the default categories for a user (idempotent)."""
    categories = []
    for name in DEFAULT_CATEGORY_NAMES:
        category, _ = Category.objects.get_or_create(user=user, name=name)
        categories.append(category)
    return categories
