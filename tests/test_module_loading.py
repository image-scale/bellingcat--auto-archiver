"""Tests for the module discovery and loading system."""

import pytest
import os
import sys

from webkeeper.core.module import ModuleFactory, LazyBaseModule, MANIFEST_FILE, DEFAULT_MANIFEST
from webkeeper.core.base_module import SetupError
from webkeeper.core import Feeder, Enricher


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "modules")


class TestModuleFactory:
    """Test ModuleFactory functionality."""

    def test_factory_creation(self):
        """Factory can be instantiated."""
        factory = ModuleFactory()
        assert factory._lazy_modules == {}
        assert factory._module_paths == []

    def test_setup_paths_adds_valid_paths(self, tmp_path):
        """setup_paths adds existing directories to search paths."""
        factory = ModuleFactory()
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        factory.setup_paths([str(modules_dir)])

        assert str(modules_dir) in factory._module_paths

    def test_setup_paths_ignores_nonexistent(self, tmp_path):
        """setup_paths ignores non-existent directories."""
        factory = ModuleFactory()
        nonexistent = str(tmp_path / "nonexistent")

        factory.setup_paths([nonexistent])

        assert nonexistent not in factory._module_paths

    def test_available_modules_empty_when_no_paths(self):
        """available_modules returns empty list when no paths configured."""
        factory = ModuleFactory()
        modules = factory.available_modules()
        assert modules == []

    def test_available_modules_finds_modules(self):
        """available_modules discovers modules with manifest files."""
        factory = ModuleFactory()
        factory.setup_paths([FIXTURES_DIR])

        modules = factory.available_modules()

        names = [m.name for m in modules]
        assert "sample_feeder" in names
        assert "sample_enricher" in names

    def test_available_modules_limit_to_modules(self):
        """available_modules can filter by module name."""
        factory = ModuleFactory()
        factory.setup_paths([FIXTURES_DIR])

        modules = factory.available_modules(limit_to_modules=["sample_feeder"])

        assert len(modules) == 1
        assert modules[0].name == "sample_feeder"

    def test_get_module_lazy_returns_lazy_module(self):
        """get_module_lazy returns LazyBaseModule without loading."""
        factory = ModuleFactory()
        factory.setup_paths([FIXTURES_DIR])

        lazy = factory.get_module_lazy("sample_feeder")

        assert isinstance(lazy, LazyBaseModule)
        assert lazy.name == "sample_feeder"
        assert lazy._instance is None

    def test_get_module_lazy_raises_for_unknown(self):
        """get_module_lazy raises IndexError for unknown modules."""
        factory = ModuleFactory()
        factory.setup_paths([FIXTURES_DIR])

        with pytest.raises(IndexError) as exc_info:
            factory.get_module_lazy("nonexistent_module")

        assert "not found" in str(exc_info.value)

    def test_get_module_lazy_caches_result(self):
        """get_module_lazy caches lazy modules."""
        factory = ModuleFactory()
        factory.setup_paths([FIXTURES_DIR])

        lazy1 = factory.get_module_lazy("sample_feeder")
        lazy2 = factory.get_module_lazy("sample_feeder")

        assert lazy1 is lazy2

    def test_get_module_loads_and_configures(self):
        """get_module loads module and calls config_setup."""
        factory = ModuleFactory()
        factory.setup_paths([FIXTURES_DIR])

        module = factory.get_module("sample_feeder", {"sample_feeder": {"urls": ["https://test.com"]}})

        assert isinstance(module, Feeder)
        assert module.name == "sample_feeder"
        assert module.urls == ["https://test.com"]


class TestLazyBaseModule:
    """Test LazyBaseModule functionality."""

    def test_manifest_property_parses_manifest(self):
        """manifest property parses __manifest__.py file."""
        factory = ModuleFactory()
        factory.setup_paths([FIXTURES_DIR])

        lazy = factory.get_module_lazy("sample_feeder")
        manifest = lazy.manifest

        assert manifest["name"] == "Sample Feeder"
        assert "feeder" in manifest["type"]
        assert manifest["version"] == "1.0.0"

    def test_manifest_property_caches_result(self):
        """manifest property caches parsed result."""
        factory = ModuleFactory()
        factory.setup_paths([FIXTURES_DIR])

        lazy = factory.get_module_lazy("sample_feeder")
        manifest1 = lazy.manifest
        manifest2 = lazy.manifest

        assert manifest1 is manifest2

    def test_type_property_returns_types(self):
        """type property returns module types from manifest."""
        factory = ModuleFactory()
        factory.setup_paths([FIXTURES_DIR])

        lazy = factory.get_module_lazy("sample_feeder")

        assert lazy.type == ["feeder"]

    def test_configs_property_returns_configs(self):
        """configs property returns configuration options."""
        factory = ModuleFactory()
        factory.setup_paths([FIXTURES_DIR])

        lazy = factory.get_module_lazy("sample_feeder")
        configs = lazy.configs

        assert "source" in configs
        assert configs["source"]["default"] == "cli"
        assert "max_items" in configs
        assert configs["max_items"]["default"] == 100

    def test_display_name_property(self):
        """display_name returns human-readable name."""
        factory = ModuleFactory()
        factory.setup_paths([FIXTURES_DIR])

        lazy = factory.get_module_lazy("sample_feeder")

        assert lazy.display_name == "Sample Feeder"

    def test_requires_setup_property(self):
        """requires_setup returns manifest value."""
        factory = ModuleFactory()
        factory.setup_paths([FIXTURES_DIR])

        lazy = factory.get_module_lazy("sample_feeder")

        assert lazy.requires_setup is False

    def test_entry_point_property(self):
        """entry_point returns module entry point."""
        factory = ModuleFactory()
        factory.setup_paths([FIXTURES_DIR])

        lazy = factory.get_module_lazy("sample_feeder")

        assert lazy.entry_point == "sample_feeder::SampleFeeder"

    def test_dependencies_property(self):
        """dependencies returns dependency requirements."""
        factory = ModuleFactory()
        factory.setup_paths([FIXTURES_DIR])

        lazy = factory.get_module_lazy("sample_enricher")

        assert "python" in lazy.dependencies
        assert "json" in lazy.dependencies["python"]

    def test_load_returns_configured_instance(self):
        """load returns fully configured module instance."""
        factory = ModuleFactory()
        factory.setup_paths([FIXTURES_DIR])

        lazy = factory.get_module_lazy("sample_feeder")
        module = lazy.load({"sample_feeder": {}})

        assert isinstance(module, Feeder)
        assert module.name == "sample_feeder"
        assert module.display_name == "Sample Feeder"
        assert hasattr(module, 'setup_called')

    def test_load_caches_instance(self):
        """load caches module instance."""
        factory = ModuleFactory()
        factory.setup_paths([FIXTURES_DIR])

        lazy = factory.get_module_lazy("sample_feeder")
        module1 = lazy.load({})
        module2 = lazy.load({})

        assert module1 is module2

    def test_load_applies_default_configs(self):
        """load applies default config values from manifest."""
        factory = ModuleFactory()
        factory.setup_paths([FIXTURES_DIR])

        lazy = factory.get_module_lazy("sample_feeder")
        module = lazy.load({})

        assert module.source == "cli"
        assert module.max_items == 100

    def test_load_merges_user_config(self):
        """load merges user config over defaults."""
        factory = ModuleFactory()
        factory.setup_paths([FIXTURES_DIR])

        lazy = factory.get_module_lazy("sample_feeder")
        module = lazy.load({"sample_feeder": {"source": "csv", "max_items": 50}})

        assert module.source == "csv"
        assert module.max_items == 50

    def test_load_calls_setup(self):
        """load calls module's setup method."""
        factory = ModuleFactory()
        factory.setup_paths([FIXTURES_DIR])

        lazy = factory.get_module_lazy("sample_feeder")
        module = lazy.load({})

        assert module.setup_called is True

    def test_repr(self):
        """LazyBaseModule has useful repr."""
        factory = ModuleFactory()
        factory.setup_paths([FIXTURES_DIR])

        lazy = factory.get_module_lazy("sample_feeder")

        assert "Sample Feeder" in repr(lazy)
        assert "sample_feeder" in repr(lazy)


class TestModuleConstants:
    """Test module-level constants."""

    def test_manifest_file_constant(self):
        """MANIFEST_FILE is correct filename."""
        assert MANIFEST_FILE == "__manifest__.py"

    def test_default_manifest_has_required_keys(self):
        """DEFAULT_MANIFEST has all required keys."""
        assert "name" in DEFAULT_MANIFEST
        assert "type" in DEFAULT_MANIFEST
        assert "configs" in DEFAULT_MANIFEST
        assert "dependencies" in DEFAULT_MANIFEST
        assert "entry_point" in DEFAULT_MANIFEST
        assert "requires_setup" in DEFAULT_MANIFEST


class TestDependencyChecking:
    """Test dependency verification."""

    def test_python_dependency_exists(self):
        """Module with available python dependency loads successfully."""
        factory = ModuleFactory()
        factory.setup_paths([FIXTURES_DIR])

        module = factory.get_module("sample_enricher", {})

        assert isinstance(module, Enricher)

    def test_missing_binary_dependency_raises(self, tmp_path):
        """Module with missing binary dependency raises SetupError."""
        modules_dir = tmp_path / "modules" / "broken_module"
        modules_dir.mkdir(parents=True)

        manifest = modules_dir / "__manifest__.py"
        manifest.write_text('''
{
    "name": "Broken Module",
    "type": ["enricher"],
    "entry_point": "broken_module::BrokenModule",
    "dependencies": {"bin": ["nonexistent_binary_xyz123"]}
}
''')

        impl = modules_dir / "broken_module.py"
        impl.write_text('''
from webkeeper.core import Enricher
class BrokenModule(Enricher):
    def enrich(self, m): pass
''')

        factory = ModuleFactory()
        factory.setup_paths([str(tmp_path / "modules")])

        with pytest.raises(SetupError) as exc_info:
            factory.get_module("broken_module", {})

        assert "nonexistent_binary_xyz123" in str(exc_info.value)
