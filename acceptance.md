# Acceptance Criteria

## Task 1: Media and Metadata classes
- [x] All criteria met (see tests/test_media.py and tests/test_metadata.py)

## Task 2: Base module system
- [x] All criteria met (see tests/test_base_modules.py)

## Task 3: Module discovery and loading system

### ModuleFactory Acceptance Criteria
- [ ] ModuleFactory.available_modules() scans module paths and returns LazyBaseModule list
- [ ] ModuleFactory.get_module_lazy(name) returns LazyBaseModule without loading code
- [ ] ModuleFactory.get_module(name, config) loads and configures a module instance
- [ ] ModuleFactory.setup_paths(paths) adds additional search paths for modules

### LazyBaseModule Acceptance Criteria
- [ ] LazyBaseModule.manifest property parses __manifest__.py and returns dict
- [ ] LazyBaseModule.type returns module type(s) from manifest
- [ ] LazyBaseModule.configs returns module configuration options from manifest
- [ ] LazyBaseModule.load(config) instantiates module, calls config_setup and setup
- [ ] LazyBaseModule checks dependencies before loading (python packages, binaries)
