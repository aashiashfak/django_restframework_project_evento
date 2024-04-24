from django.core.cache import cache

def cached_queryset(key, queryset_fn, timeout=None):
    """
    Function to cache queryset.
    :param key: Cache key
    :param queryset_fn: Function to generate queryset
    :param timeout: Timeout value for cache
    :return: Cached queryset
    """
    queryset = cache.get(key)
    print(key)
    count = 0

    if queryset is None:
        count += 1
        queryset = queryset_fn()
        print("Fetched from database", count)
        cache.set(key, queryset, timeout=timeout)
        print(queryset)
    else:
        count += 1
        print("Fetched from cache", count)
    return queryset