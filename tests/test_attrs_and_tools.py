"""Tests for Attrs navigation (including nested access) and the module-walking tools."""

import types

import pytest

import guide
from guide import Attrs
from guide.tools import (
    internal_modules,
    is_an_obj_of_module,
    is_hashable,
    print_attrs_info,
    recollect,
)


class Thing:
    public = 1
    _hidden = 2

    def method(self, a, b=2):
        return a + b


def test_attrs_lists_public_names_and_nests():
    a = Attrs(Thing)
    assert sorted(a) == ["method", "public"]
    nested = a["method"]
    assert isinstance(nested, Attrs)  # nested access keeps the public Attrs type


def test_attrs_nested_items_work_on_modules():
    a = Attrs(guide)
    tools = a["tools"]
    assert hasattr(tools, "items")
    assert any(k == "recollect" for k, _ in tools.items())


def test_attrs_repr_and_deprecated_src():
    a = Attrs(Thing)
    assert repr(a).startswith("Attrs(")
    with pytest.warns(DeprecationWarning):
        assert a.src is Thing


def test_module_from_path(tmp_path):
    f = tmp_path / "mod_x.py"
    f.write_text("alpha = 1\n_beta = 2\n")
    a = Attrs.module_from_path(str(f), name="mod_x")
    assert "alpha" in list(a) and "_beta" not in list(a)


def test_internal_modules_finds_submodules():
    paths = set(internal_modules(guide))
    assert ("tools",) in paths and ("base",) in paths


def test_print_attrs_info_lists_methods_and_props(capsys):
    print_attrs_info(Thing)
    out = capsys.readouterr().out
    assert "method" in out and "public" in out and "_hidden" not in out
    print_attrs_info(Thing, include_hidden=True)
    assert "_hidden" in capsys.readouterr().out


def test_is_hashable_and_module_membership():
    assert is_hashable(1) and not is_hashable([])
    assert is_an_obj_of_module(Attrs, guide)
    assert not is_an_obj_of_module(len, guide)


def test_recollect_collects_callables():
    mod = types.ModuleType("m")
    mod.f = lambda: 1
    mod.n = 3
    found = list(recollect(mod))
    assert any(callable(x) for x in found)
