
# guide
Simple object to navigate complex python objects


To install:	```pip install guide```


# Examples

Object that provides a mapping interface to the attributes of python object.

The keys will be the names of the attributes and the values will be ``Attrs`` instances of said attributes.

```pydocstring
>>> import guide
>>> from guide import Attrs
>>> a = Attrs(guide)
>>> sorted(a)  # you would usually use ``list`` instead of ``sorted`` but the latter is used for test consistency
['Attrs', 'ObjReader', 'base', 'util']
>>> aa = a['Attrs']
>>> sorted(aa)
['get', 'head', 'items', 'keys', 'module_from_path', 'update_keys_cache', 'values']
```

Here's how you could implement a generator of paths (tuples) of internal module of a given module:

```python
def internal_modules(module, path=()):
    if not isinstance(module, Attrs):
        module = Attrs(module)
    prefix = module.src.__name__
    for k, v in module.items():
        if inspect.ismodule(v.src) and v.src.__name__.startswith(prefix):
            yield path + (k,)
            yield from internal_modules(v, path=path + (k,))
```

```pydocstring
>>> import guide
>>> for path in internal_modules(guide):
...     print(path)
('tools',)
('tests',)
('tests', 'simple_tests')
('base',)
('util',)
```
