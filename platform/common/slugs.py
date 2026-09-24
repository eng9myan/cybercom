from django.utils.text import slugify


def unique_slugify(queryset, base_text, *, exclude_pk=None):
    """Derive a slug from `base_text` that doesn't collide with any row
    already in `queryset` (the caller passes an already tenant/parent-scoped
    queryset on the model's own manager) -- appends -2, -3, ... until free.

    Guards against the `unique_together` constraint every slugified model in
    cycom uses: a bare `slugify(title)` with no collision check raises an
    unhandled IntegrityError the moment two rows would slugify the same
    (e.g. two guests both titling a public forum thread "Hello World").
    """
    base = slugify(base_text) or "item"
    slug = base
    n = 2
    qs = queryset.exclude(pk=exclude_pk) if exclude_pk else queryset
    while qs.filter(slug=slug).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug
