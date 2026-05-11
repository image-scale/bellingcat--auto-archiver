# Todo

## Plan
Start with the core data structures (Media and Metadata), then implement the base module classes and module loading system, followed by the configuration parser and orchestrator. Finally, add built-in modules one at a time. Each task delivers user-facing functionality with working tests.

## Tasks
- [>] Task 1: Implement Media and Metadata classes for representing archived content with properties, URL tracking, media type detection, merging capabilities, and JSON serialization
- [ ] Task 2: Implement the base module system with BaseModule and module type classes (Feeder, Extractor, Enricher, Database, Storage, Formatter) that define the plugin interfaces
- [ ] Task 3: Implement the module discovery and loading system with manifest parsing, lazy loading, dependency checking, and factory pattern for instantiation
- [ ] Task 4: Implement the configuration system with YAML parsing, CLI argument generation from module configs, config merging, and validation
- [ ] Task 5: Implement the orchestrator that coordinates the full archiving pipeline - feeding items, extracting content, enriching, storing, formatting, and database reporting
- [ ] Task 6: Implement the CLI feeder module that takes URLs from command line arguments and yields Metadata objects for archiving
- [ ] Task 7: Implement the console database module that logs archiving status (started, failed, done) to console output
- [ ] Task 8: Implement the hash enricher module that calculates cryptographic hashes (SHA-256, SHA3-512) for archived media files
- [ ] Task 9: Implement the local storage module that saves archived media files to the local filesystem with configurable path and filename strategies
- [ ] Task 10: Implement the mute formatter module that serves as a no-op formatter returning None
- [ ] Task 11: Implement the generic extractor module that uses yt-dlp to download videos and metadata from supported websites
