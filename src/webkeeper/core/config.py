"""
Configuration system for loading, parsing, and merging YAML configs.

The config system handles reading YAML configuration files, merging
CLI arguments with file-based config, and converting between nested
dict and dot-notation formats for argparse compatibility.
"""

from __future__ import annotations
from copy import deepcopy
import os

from ruamel.yaml import YAML, CommentedMap

from .base_module import MODULE_TYPES


_yaml = YAML()

DEFAULT_CONFIG_FILE = "config.yaml"

EMPTY_CONFIG = _yaml.load(
    """
# WebKeeper Configuration

steps:"""
    + "".join([f"\n  {module_type}s: []" for module_type in MODULE_TYPES])
    + """

authentication: {}

logging:
  level: INFO
"""
)


def read_yaml(yaml_filename: str) -> CommentedMap:
    """
    Reads a YAML configuration file.

    Args:
        yaml_filename: Path to YAML file

    Returns:
        Parsed configuration as CommentedMap.
        Returns empty config structure if file doesn't exist.
    """
    config = None
    try:
        with open(yaml_filename, "r", encoding="utf-8") as f:
            config = _yaml.load(f)
    except FileNotFoundError:
        pass

    if not config:
        config = deepcopy(EMPTY_CONFIG)

    return config


def store_yaml(config: CommentedMap, yaml_filename: str) -> None:
    """
    Writes configuration to a YAML file.

    Args:
        config: Configuration to save
        yaml_filename: Path to write to
    """
    config_to_save = deepcopy(config)

    directory = os.path.dirname(yaml_filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    config_to_save.pop("urls", None)

    with open(yaml_filename, "w", encoding="utf-8") as f:
        _yaml.dump(config_to_save, f)


def is_dict_type(value) -> bool:
    """Checks if value is dict-like."""
    return isinstance(value, (dict, CommentedMap))


def is_list_type(value) -> bool:
    """Checks if value is list-like."""
    return isinstance(value, (list, tuple, set))


def to_dot_notation(yaml_conf: CommentedMap | dict) -> dict:
    """
    Flattens nested dict to dot-separated keys.

    Example: {"a": {"b": 1}} -> {"a.b": 1}

    Args:
        yaml_conf: Nested configuration dict

    Returns:
        Flattened dict with dot-notation keys
    """
    dotdict = {}

    def process_subdict(subdict, prefix=""):
        for key, value in subdict.items():
            if is_dict_type(value):
                process_subdict(value, f"{prefix}{key}.")
            else:
                dotdict[f"{prefix}{key}"] = value

    process_subdict(yaml_conf)
    return dotdict


def from_dot_notation(dotdict: dict) -> dict:
    """
    Restores nested dict from dot-separated keys.

    Example: {"a.b": 1} -> {"a": {"b": 1}}

    Args:
        dotdict: Flattened dict with dot-notation keys

    Returns:
        Nested configuration dict
    """
    normal_dict = {}

    def add_part(key, value, current_dict):
        if "." in key:
            key_parts = key.split(".", 1)
            current_dict.setdefault(key_parts[0], {})
            add_part(key_parts[1], value, current_dict[key_parts[0]])
        else:
            current_dict[key] = value

    for key, value in dotdict.items():
        add_part(key, value, normal_dict)

    return normal_dict


def merge_dicts(dotdict: dict, yaml_dict: CommentedMap) -> CommentedMap:
    """
    Merges CLI arguments (dot notation) with YAML config.

    Lists are extended rather than replaced. Dicts are recursively merged.

    Args:
        dotdict: CLI arguments in dot notation
        yaml_dict: YAML configuration

    Returns:
        Merged configuration
    """
    yaml_dict = deepcopy(yaml_dict)

    def update_dict(subdict, yaml_subdict):
        for key, value in subdict.items():
            if key not in yaml_subdict:
                yaml_subdict[key] = value
                continue

            if key == "steps":
                for module_type, modules in value.items():
                    yaml_subdict[key][module_type] = modules
                continue

            if is_dict_type(value):
                update_dict(value, yaml_subdict[key])
            elif is_list_type(value):
                for item in value:
                    if item not in yaml_subdict[key]:
                        yaml_subdict[key].append(item)
            else:
                yaml_subdict[key] = value

    update_dict(from_dot_notation(dotdict), yaml_dict)
    return yaml_dict


def is_valid_config(config: CommentedMap) -> bool:
    """Checks if config has meaningful content beyond defaults."""
    if not config:
        return False
    if config == EMPTY_CONFIG:
        return False
    return True
