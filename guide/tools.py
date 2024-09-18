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

NO_SIGNATURE = type('NoSignature', (), {})()


def argument_names(func, is_a_method):
    from i2 import Sig

    try:
        return Sig(func).names[bool(is_a_method) :]
    except ValueError:
        return NO_SIGNATURE


def print_attrs_info(obj, attrs=None, include_hidden=False, deep=True):
    """
    Print
    :param obj: An object (type or instance) you want to have information on
    :param attrs: The specific attributes you want to know about.
        If None, will use "all". The next arguments control what that means
    :param include_hidden: All? No: Just the non hidden ones by defualt (i.e. not
    starting with an underscore). Unless you specify `include_hidden=True`.
    :param deep: True by default. If False, "all" will not include the attributes
        defined in parents of the object.

    If (as happens with some builtins) a method has no signature, and therefore we
    can't display argument names, `NO_SIGNATURE` will be displayed instead.
    If nothing is displayed, it means that the metho takes no arguments.

    >>> from collections import namedtuple
    >>> print_attrs_info(namedtuple, include_hidden=True)  # doctest: +NORMALIZE_WHITESPACE
    ----- Methods -----
             __call__: args, kwargs
            __class__: code, globals, name, argdefs, closure
          __delattr__: name
              __dir__:
               __eq__: value
           __format__: format_spec
               __ge__: value
              __get__: instance, owner
     __getattribute__: name
               __gt__: value
             __hash__:
             __init__: args, kwargs
    __init_subclass__: NO_SIGNATURE
               __le__: value
               __lt__: value
               __ne__: value
              __new__: args, kwargs
           __reduce__:
        __reduce_ex__: protocol
             __repr__:
          __setattr__: name, value
           __sizeof__:
              __str__:
     __subclasshook__: NO_SIGNATURE
    ------ Props ------
    __annotations__
    __closure__
    __code__
    __defaults__
    __dict__
    __doc__
    __globals__
    __kwdefaults__
    __module__
    __name__
    __qualname__


    If you specify an object that is not a type, it will do the same.
    By default, `include_hidden=False`, so this will not show any names starting with
    an underscore:

    >>> print_attrs_info([1, 2, 3])  # doctest: +NORMALIZE_WHITESPACE
    ----- Methods -----
     append: object
      clear:
       copy:
      count: value
     extend: iterable
      index: value, start, stop
     insert: index, object
        pop: index
     remove: value
    reverse:
       sort: key, reverse
    ------ Props ------

    """
    if attrs is None:
        if deep:
            attrs = dir(obj)
        else:
            attrs = vars(obj)
        if not include_hidden:
            attrs = [a for a in attrs if not a.startswith('_')]
    if not attrs:
        return
    attr_obj = partial(getattr, obj)
    attrs = list(attrs)
    methods = list(filter(lambda a: callable(attr_obj(a)), attrs))
    props = list(filter(lambda a: not callable(attr_obj(a)), attrs))
    n = max(map(len, attrs))
    is_a_method = int(isinstance(obj, type))
    print('----- Methods -----')
    for a in methods:
        func = getattr(obj, a)
        argnames = argument_names(func, is_a_method)
        if argnames is NO_SIGNATURE:
            argname_str = 'NO_SIGNATURE'
        else:
            argname_str = ', '.join(argnames)
        print(f'{a}'.rjust(n) + f': {argname_str}')
    print('------ Props ------')
    for a in props:
        print(f'{a}')


# TODO: Finish this, and use in print_attrs_info
def attrs_info_dict(obj, attrs=None, include_hidden=False, deep=True):
    """Yield information dicts about the attributes of an object"""

    if attrs is None:
        if deep:
            attrs = dir(obj)
        else:
            attrs = vars(obj)
        if not include_hidden:
            attrs = [a for a in attrs if not a.startswith('_')]
    if not attrs:
        return
    attr_obj = partial(getattr, obj)
    attrs = list(attrs)

    for method in filter(lambda a: callable(attr_obj(a)), attrs):
        yield {
            'kind': 'method',
            'name': method,
            'argnames': argument_names(getattr(obj, method)),
        }
    for prop in filter(lambda a: not callable(attr_obj(a)), attrs):
        yield {'kind': 'property', 'name': prop}


def ensure_module(module_src: ModuleSource):
    if isinstance(module_src, ModuleType):
        return module_src
    elif isinstance(module_src, str):
        return import_module(module_src)
    else:
        raise TypeError(
            f"Don't know how to cast this type to a module object: {type(module_src)}"
        )


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


@wrap_kvs(
    obj_of_data=lambda obj: {
        k: getattr(obj, k) for k in dir(obj) if not k.startswith('_')
    }
)
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


def recollect(
    obj,
    collect_condition: Callable = lambda k, v: isinstance(v, (Callable, ModuleType)),
    visit_condition: Callable = lambda k, v: isinstance(v, ModuleType),
    visited=None,
):
    if visited is None:
        visited = set()
    else:
        visited.add(obj)
    for k, a in Attrs(obj).items():
        v = a._obj
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
        collect_condition=lambda k, v: isinstance(v, Callable)
        and is_an_obj_of_specific_module(v),
        visit_condition=lambda k, v: isinstance(v, ModuleType)
        and v.__name__.startswith(module.__name__),
    )
