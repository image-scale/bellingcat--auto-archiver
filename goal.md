# Goal

## Project
auto-archiver — a python project.

## Description
Auto-archiver is a Python tool to automatically archive content from the web. It takes URLs from various sources (CLI, CSV files, Google Sheets), extracts content using extractors (video downloaders, web scrapers), enriches the archived data with additional metadata (hashes, timestamps, thumbnails), stores media files locally or remotely, and formats results for reporting. The architecture is modular and plugin-based, with a central orchestrator coordinating feeders, extractors, enrichers, databases, storages, and formatters.

## Scope
- Core data structures: Media and Metadata classes for representing archived content
- Module system: Base classes for feeders, extractors, enrichers, databases, storages, and formatters
- Plugin discovery and loading via manifest files
- Configuration system: YAML-based config with CLI argument parsing
- Orchestrator: Central coordinator that runs the archiving pipeline
- Built-in modules: CLI feeder, console database, hash enricher, local storage, mute formatter, and generic extractor
- Test suite covering all core functionality
