# Acceptance Criteria

## Task 1: Media and Metadata classes
- [x] All criteria met (see tests/test_media.py and tests/test_metadata.py)

## Task 2: Base module system

### BaseModule Acceptance Criteria
- [ ] BaseModule.config_setup(config) stores config and sets attributes from config[module_name]
- [ ] BaseModule provides MODULE_TYPES constant listing all module types
- [ ] BaseModule.setup() can be overridden for module-specific initialization
- [ ] BaseModule.auth_for_site(url) retrieves authentication info for a domain from config

### Module Type Acceptance Criteria
- [ ] Feeder base class has abstract __iter__ method returning Metadata objects
- [ ] Extractor base class has abstract download(item) method returning Metadata
- [ ] Extractor.sanitize_url(url) cleans/transforms URLs
- [ ] Extractor.download_from_url(url, filename) downloads file to local path
- [ ] Enricher base class has abstract enrich(metadata) method
- [ ] Database base class has started/failed/aborted/done/fetch methods
- [ ] Storage base class has abstract get_cdn_url and uploadf methods
- [ ] Storage.store(media, url, metadata) coordinates key generation and upload
- [ ] Formatter base class has abstract format(metadata) returning Media
