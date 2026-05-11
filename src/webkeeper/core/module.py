"""
Module factory and lazy loading system for plugin modules.

The module system supports discovering, loading, and instantiating modules
from manifest files. Modules are discovered from configurable paths and
can be lazily loaded to defer dependency resolution until needed.
"""

from __future__ import annotations
import ast
import os
import sys
import shutil
import subprocess
from dataclasses import dataclass
from importlib.util import find_spec
from os.path import join
from typing import List, TYPE_CHECKING, Type
from copy import copy

from .base_module import BaseModule, SetupError, MODULE_TYPES

if TYPE_CHECKING:
    pass


MANIFEST_FILE = "__manifest__.py"

DEFAULT_MANIFEST = {
    "name": "",
    "author": "Unknown",
    "type": [],
    "requires_setup": True,
    "description": "",
    "dependencies": {},
    "entry_point": "",
    "version": "1.0",
    "configs": {},
}


class ModuleFactory:
    """
    Factory for discovering and loading modules.

    The factory scans configured paths for modules with valid manifest files
    and provides lazy loading to defer dependency resolution.
    """

    def __init__(self):
        self._lazy_modules = {}
        self._module_paths = []

    def setup_paths(self, paths: List[str]) -> None:
        """
        Adds additional paths to search for modules.

        Args:
            paths: List of directory paths to search
        """
        for path in paths:
            if not os.path.exists(path):
                continue
            if path not in self._module_paths:
                self._module_paths.append(path)

    def get_module(self, module_name: str, config: dict) -> Type[BaseModule]:
        """
        Gets and configures a module instance.

        This loads the module, checks dependencies, and calls config_setup.

        Args:
            module_name: Name of module to load
            config: Configuration dictionary

        Returns:
            Configured module instance
        """
        return self.get_module_lazy(module_name).load(config)

    def get_module_lazy(self, module_name: str, suppress_warnings: bool = False) -> "LazyBaseModule":
        """
        Gets a lazy module reference without loading code.

        Args:
            module_name: Name of module to get
            suppress_warnings: Whether to suppress not-found warnings

        Returns:
            LazyBaseModule reference

        Raises:
            IndexError: If module not found
        """
        if module_name in self._lazy_modules:
            return self._lazy_modules[module_name]

        available = self.available_modules(
            limit_to_modules=[module_name],
            suppress_warnings=suppress_warnings
        )

        if not available:
            raise IndexError(f"Module '{module_name}' not found. Are you sure it exists?")

        return available[0]

    def available_modules(
        self,
        limit_to_modules: List[str] = None,
        suppress_warnings: bool = False
    ) -> List["LazyBaseModule"]:
        """
        Scans module paths and returns available modules.

        Args:
            limit_to_modules: Only return modules with these names
            suppress_warnings: Whether to suppress not-found warnings

        Returns:
            List of LazyBaseModule objects
        """
        if limit_to_modules is None:
            limit_to_modules = []

        all_modules = []

        for module_folder in self._module_paths:
            if not os.path.isdir(module_folder):
                continue

            try:
                possible_modules = os.listdir(module_folder)
            except FileNotFoundError:
                continue

            for possible_module in possible_modules:
                if limit_to_modules and possible_module not in limit_to_modules:
                    continue

                module_path = join(module_folder, possible_module)

                if not os.path.isfile(join(module_path, MANIFEST_FILE)):
                    continue

                if possible_module in self._lazy_modules:
                    all_modules.append(self._lazy_modules[possible_module])
                    continue

                lazy_module = LazyBaseModule(
                    possible_module,
                    module_path,
                    factory=self
                )
                self._lazy_modules[possible_module] = lazy_module
                all_modules.append(lazy_module)

        return all_modules


@dataclass
class LazyBaseModule:
    """
    Lazy reference to a module that defers loading until needed.

    Provides access to module metadata from the manifest without
    loading the actual module code or checking dependencies.
    """

    name: str
    path: str
    module_factory: ModuleFactory

    _manifest: dict = None
    _instance: BaseModule = None
    _entry_point: str = None
    description: str = ""
    version: str = "1.0"

    def __init__(self, module_name: str, path: str, factory: ModuleFactory):
        self.name = module_name
        self.path = path
        self.module_factory = factory
        self._manifest = None
        self._instance = None
        self._entry_point = None
        self.description = ""
        self.version = "1.0"

    @property
    def type(self) -> List[str]:
        """Returns module type(s) from manifest."""
        return self.manifest.get("type", [])

    @property
    def entry_point(self) -> str:
        """Returns entry point for module instantiation."""
        if not self._entry_point and not self.manifest.get("entry_point"):
            class_name = "".join(
                word.capitalize()
                for word in self.name.replace("_", " ").split()
            )
            self._entry_point = f"{self.name}::{class_name}"
        return self._entry_point or self.manifest.get("entry_point", "")

    @property
    def dependencies(self) -> dict:
        """Returns dependency requirements from manifest."""
        return self.manifest.get("dependencies", {})

    @property
    def configs(self) -> dict:
        """Returns configuration options from manifest."""
        return self.manifest.get("configs", {})

    @property
    def requires_setup(self) -> bool:
        """Returns whether module requires additional setup."""
        return self.manifest.get("requires_setup", True)

    @property
    def display_name(self) -> str:
        """Returns human-readable module name."""
        return self.manifest.get("name", "") or self.name

    @property
    def manifest(self) -> dict:
        """
        Parses and returns the module manifest.

        The manifest is cached after first parse.
        """
        if self._manifest:
            return self._manifest

        manifest = copy(DEFAULT_MANIFEST)

        manifest_path = join(self.path, MANIFEST_FILE)
        with open(manifest_path) as f:
            try:
                manifest.update(ast.literal_eval(f.read()))
            except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError) as e:
                raise ValueError(f"Error loading manifest from {manifest_path}: {e}") from e

        self._manifest = manifest
        self._entry_point = manifest.get("entry_point", "")
        self.description = manifest.get("description", "")
        self.version = manifest.get("version", "1.0")

        return manifest

    def load(self, config: dict) -> BaseModule:
        """
        Loads and configures the module.

        Checks dependencies, imports the module, instantiates the class,
        and calls config_setup and setup.

        Args:
            config: Configuration dictionary

        Returns:
            Configured module instance
        """
        if self._instance:
            return self._instance

        self._check_dependencies(config)

        sys.path.insert(0, os.path.dirname(self.path))

        try:
            file_name, class_name = self.entry_point.split("::")
            module_qualname = f"{self.name}.{file_name}"

            __import__(module_qualname, fromlist=[class_name])

            instance: BaseModule = getattr(sys.modules[module_qualname], class_name)()
        finally:
            if os.path.dirname(self.path) in sys.path:
                sys.path.remove(os.path.dirname(self.path))

        self._instance = instance

        instance.name = self.name
        instance.display_name = self.display_name
        instance.module_factory = self.module_factory

        default_config = {
            k: v.get("default")
            for k, v in self.configs.items()
            if "default" in v
        }
        config[self.name] = default_config | config.get(self.name, {})

        instance.config_setup(config)
        instance.setup()

        return instance

    def _check_dependencies(self, config: dict) -> None:
        """Checks that all dependencies are available."""
        python_deps = self.dependencies.get("python", [])
        for dep in python_deps:
            dep = dep.strip()
            if not dep:
                continue

            if find_spec(dep):
                continue

            try:
                self.module_factory.get_module_lazy(dep, suppress_warnings=True)
            except IndexError:
                raise SetupError(
                    f"Module '{self.name}' requires Python package '{dep}' which is not available."
                )

        bin_deps = self.dependencies.get("bin", [])
        for dep in bin_deps:
            dep = dep.strip()
            if not dep:
                continue

            if not shutil.which(dep):
                raise SetupError(
                    f"Module '{self.name}' requires binary '{dep}' which is not available."
                )

    def __repr__(self) -> str:
        return f"Module<'{self.display_name}' ({self.name})>"
