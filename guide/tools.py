import inspect

from guide import Attrs


def internal_modules(module, path=()):
    """A generator of paths (tuples) of internal module of a given module

    >>> import guide
    >>> for path in internal_modules(guide):
    ...     print(path)
    ('tools',)
    ('tests',)
    ('tests', 'simple_tests')
    ('base',)
    ('util',)
    """
    if not isinstance(module, Attrs):
        module = Attrs(module)
    prefix = module.src.__name__
    for k, v in module.items():
        if inspect.ismodule(v.src) and v.src.__name__.startswith(prefix):
            yield path + (k,)
            yield from internal_modules(v, path=path + (k,))
