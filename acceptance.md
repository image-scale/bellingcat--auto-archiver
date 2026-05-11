# Acceptance Criteria

## Task 1: Media and Metadata classes
- [x] All criteria met (see tests/test_media.py and tests/test_metadata.py)

## Task 2: Base module system
- [x] All criteria met (see tests/test_base_modules.py)

## Task 3: Module discovery and loading system
- [x] All criteria met (see tests/test_module_loading.py)

## Task 4: Configuration system

### Config Parsing Acceptance Criteria
- [ ] read_yaml(filename) loads YAML config file and returns dict
- [ ] store_yaml(config, filename) saves config to YAML file
- [ ] read_yaml with missing file returns default empty config structure
- [ ] Config includes steps section with lists for each module type

### Config Merging Acceptance Criteria
- [ ] to_dot_notation(config) flattens nested dict to dot-separated keys
- [ ] from_dot_notation(dotdict) restores nested dict from flattened
- [ ] merge_dicts combines CLI args with yaml config, extending lists
