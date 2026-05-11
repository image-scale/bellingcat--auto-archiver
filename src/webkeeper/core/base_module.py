"""
Base module class that all plugin modules inherit from.

All modules in the archiving framework extend BaseModule, which provides
common functionality for configuration setup, authentication handling,
and module identification. Specific module types (Feeder, Extractor, etc.)
add their own abstract methods.
"""

from __future__ import annotations
from abc import ABC
from copy import deepcopy
from typing import Any, Mapping, TYPE_CHECKING

if TYPE_CHECKING:
    from .module import ModuleFactory


MODULE_TYPES = ["feeder", "extractor", "enricher", "database", "storage", "formatter"]


class ArchiveError(Exception):
    """Base exception for archiving errors."""
    pass


class SetupError(ArchiveError):
    """Raised when module setup fails."""
    pass


class BaseModule(ABC):
    """
    Base class for all archiving modules.

    All modules should inherit from this class and potentially one of the
    type-specific base classes (Feeder, Extractor, etc.). Modules are
    configured via config_setup() and can implement setup() for additional
    initialization.

    Attributes:
        config: Module configuration dictionary
        authentication: Authentication settings dictionary
        name: Module's registered name
        display_name: Human-readable module name
        module_factory: Factory for loading other modules
        tmp_dir: Temporary directory for this archiving session
    """

    MODULE_TYPES = MODULE_TYPES

    config: Mapping[str, Any]
    authentication: Mapping[str, Mapping[str, str]]
    name: str
    display_name: str
    module_factory: "ModuleFactory"
    tmp_dir: str = None

    @property
    def storages(self) -> list:
        """Returns list of configured storages."""
        return self.config.get("storages", [])

    def config_setup(self, config: dict) -> None:
        """
        Configures the module from the provided configuration.

        Each module receives a deep copy of the config to prevent cross-module
        interference. Module-specific settings from config[self.name] are
        set as instance attributes.

        Args:
            config: Full configuration dictionary
        """
        config = deepcopy(config)
        authentication = deepcopy(config.pop("authentication", {}))

        self.authentication = authentication
        self.config = config

        module_config = config.get(self.name, {})
        for key, val in module_config.items():
            setattr(self, key, val)

    def setup(self) -> None:
        """
        Performs module-specific initialization.

        Override this method in subclasses to perform initialization that
        requires configuration values, such as authenticating with services
        or validating settings.
        """
        pass

    def auth_for_site(self, site: str, extract_cookies: bool = True) -> Mapping[str, Any]:
        """
        Retrieves authentication information for a given site.

        Looks up the site in the authentication config using the domain.
        Falls back to checking with and without 'www.' prefix.

        Args:
            site: URL or domain to get authentication for
            extract_cookies: Whether to extract cookies from browser/file

        Returns:
            Dictionary containing authentication info like username, password,
            api_key, cookie, etc. Empty dict if no auth configured.
        """
        from urllib.parse import urlparse

        parsed = urlparse(site)
        domain = parsed.netloc if parsed.netloc else site
        domain = domain.removeprefix("www.")

        authdict = {}

        for to_try in [site, domain, f"www.{domain}"]:
            if to_try in self.authentication:
                authdict.update(self.authentication[to_try])
                break

        return authdict

    def __repr__(self) -> str:
        module_name = getattr(self, 'display_name', getattr(self, 'name', self.__class__.__name__))
        return f"Module<'{module_name}'>"
