
def copy_attrs(target, source, attrs, raise_error_if_an_attr_is_missing=True):
    """Copy attributes from one object to another.

    >>> class A:
    ...     x = 0
    >>> class B:
    ...     x = 1
    ...     yy = 2
    ...     zzz = 3
    >>> dict_of = lambda o: {a: getattr(o, a) for a in dir(A) if not a.startswith('_')}
    >>> dict_of(A)
    {'x': 0}
    >>> copy_attrs(A, B, 'yy')
    >>> dict_of(A)
    {'x': 0, 'yy': 2}
    >>> copy_attrs(A, B, ['x', 'zzz'])
    >>> dict_of(A)
    {'x': 1, 'yy': 2, 'zzz': 3}

    But if you try to copy something that `B` (the source) doesn't have, copy_attrs will complain:
    >>> copy_attrs(A, B, 'this_is_not_an_attr')
    Traceback (most recent call last):
        ...
    AttributeError: type object 'B' has no attribute 'this_is_not_an_attr'

    If you tell it not to complain, it'll just ignore attributes that are not in source.
    >>> copy_attrs(A, B, ['nothing', 'here', 'exists'], raise_error_if_an_attr_is_missing=False)
    >>> dict_of(A)
    {'x': 1, 'yy': 2, 'zzz': 3}
    """
    if isinstance(attrs, str):
        attrs = (attrs,)
    if raise_error_if_an_attr_is_missing:
        filt = lambda a: True
    else:
        filt = lambda a: hasattr(source, a)
    for a in filter(filt, attrs):
        setattr(target, a, getattr(source, a))
