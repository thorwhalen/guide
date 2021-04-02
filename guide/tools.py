import inspect
from types import ModuleType
from typing import Callable
from functools import partial

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


from guide import Attrs
from types import ModuleType
from typing import Callable
from functools import partial


def is_hashable(obj):
    try:
        hash(obj)
        return True
    except TypeError:
        return False


def recollect(obj,
              collect_condition: Callable = lambda k, v: isinstance(v, Callable),
              visit_condition: Callable = lambda k, v: isinstance(v, ModuleType),
              visited=None):
    if visited is None:
        visited = set()
    else:
        visited.add(obj)
    for k, a in Attrs(obj).items():
        v = a.src
        if collect_condition(k, v):
            yield v
        if visit_condition(k, v) and v not in visited:
            yield from recollect(v, collect_condition, visit_condition, visited)


def is_an_obj_of_module(obj, module):
    return obj.__module__.startswith(module.__name__)


def submodule_callables(module):
    r"""Generator of callable objects of submodules of module

    >>> import guide
    >>> print(*sorted(set(x.__name__ for x in submodule_callables(guide))), sep='\n')
    Attrs
    ObjReader
    copy_attrs
    internal_modules
    is_an_obj_of_module
    is_hashable
    not_underscore_prefixed
    recollect
    submodule_callables
    """
    is_an_obj_of_specific_module = partial(is_an_obj_of_module, module=module)
    yield from recollect(
        module,
        collect_condition=lambda k, v: isinstance(v, Callable) and is_an_obj_of_specific_module(v),
        visit_condition=lambda k, v: isinstance(v, ModuleType) and v.__name__.startswith(module.__name__)
    )
