"""Tools built with guide"""

import inspect
from types import ModuleType
from typing import Callable, Union
from functools import partial
from importlib import import_module
from dataclasses import dataclass

from dol import KvReader, cached_keys, filt_iter, wrap_kvs
from guide import Attrs

ModuleSource = Union[ModuleType, str]


def ensure_module(module_src: ModuleSource):
    if isinstance(module_src, ModuleType):
        return module_src
    elif isinstance(module_src, str):
        return import_module(module_src)
    else:
        raise TypeError(f"Don't know how to cast this type to a module object: {type(module_src)}")


@cached_keys
@dataclass
class Modules(KvReader):
    src: ModuleSource
    src_name: str = None

    def __post_init__(self):
        self.src = ensure_module(self.src)
        self.src_name = self.src_name or self.src.__name__

    def __iter__(self):
        for module_path_tuple in internal_modules(self.src):
            yield '.'.join((self.src_name, *module_path_tuple))

    def __getitem__(self, k):
        return import_module(k)


@wrap_kvs(obj_of_data=lambda obj: {k: getattr(obj, k) for k in dir(obj)})
class ModuleAllAttrs(Modules):
    """Keys are module strings and values are {attr_name: attr_obj,...} dicts of the attributes of the module"""


@wrap_kvs(obj_of_data=lambda obj: {k: getattr(obj, k) for k in dir(obj) if not k.startswith('_')})
class ModuleAttrs(Modules):
    """Like ModuleAllAttrs but will only give you attributes whose names don't start with an underscore."""


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


def is_hashable(obj):
    try:
        hash(obj)
        return True
    except TypeError:
        return False


def recollect(obj,
              collect_condition: Callable = lambda k, v: isinstance(v, (Callable, ModuleType)),
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
        # else:
        #     print(f"Not including {v}")
        if visit_condition(k, v) and v not in visited:
            yield from recollect(v, collect_condition, visit_condition, visited)


def is_an_obj_of_module(obj, module):
    return (getattr(obj, '__module__', '') or '').startswith(module.__name__)


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
