import os
from py2store import cached_keys, KvReader

from guide.util import copy_attrs


def not_underscore_prefixed(x):
    return not x.startswith("_")


class ObjReader(KvReader):
    def __init__(self, obj):
        self.src = obj
        copy_attrs(
            target=self,
            source=self.src,
            attrs=("__name__", "__qualname__", "__module__"),
            raise_error_if_an_attr_is_missing=False
        )

    def __repr__(self):
        return f"{self.__class__.__qualname__}({self.src})"

    @property
    def _source(self):
        from warnings import warn

        warn("Deprecated: Use .src instead of ._source", DeprecationWarning, 2)
        return self.src


# Pattern: Recursive navigation
# Note moved from py2store.sources
@cached_keys(keys_cache=set, name="Attrs")
class Attrs(ObjReader):
    """Object that provides a mapping interface to the attributes of python object.
    The keys will be the names of the attributes and the values will be ``Attrs`` instances of said attributes.

    >>> import guide
    >>> from guide import Attrs
    >>> a = Attrs(guide)
    >>> sorted(a)  # you would usually use ``list`` instead of ``sorted`` but the latter is used for test consistency
    ['Attrs', 'ObjReader', 'base', 'util']
    >>> aa = a['Attrs']
    >>> sorted(aa)
    ['get', 'head', 'items', 'keys', 'module_from_path', 'update_keys_cache', 'values']

    """
    def __init__(self, obj, key_filt=not_underscore_prefixed):
        super().__init__(obj)
        self._key_filt = key_filt

    @classmethod
    def module_from_path(
            cls, path, key_filt=not_underscore_prefixed, name=None, root_path=None
    ):
        import importlib.util

        if name is None:
            if root_path is not None:
                try:
                    name = _path_to_module_str(path, root_path)
                except Exception:
                    name = "fake.module.name"
        spec = importlib.util.spec_from_file_location(name, path)
        foo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(foo)
        return cls(foo, key_filt)

    def __iter__(self):
        yield from filter(self._key_filt, dir(self.src))

    def __getitem__(self, k):
        return self.__class__(getattr(self.src, k))

    def __repr__(self):
        return f"{self.__class__.__qualname__}({self.src}, {self._key_filt})"


def _path_to_module_str(path, root_path):
    assert path.endswith(".py")
    path = path[:-3]
    if root_path.endswith(psep):
        root_path = root_path[:-1]
    root_path = os.path.dirname(root_path)
    len_root = len(root_path) + 1
    path_parts = path[len_root:].split(psep)
    if path_parts[-1] == "__init__.py":
        path_parts = path_parts[:-1]
    return ".".join(path_parts)
