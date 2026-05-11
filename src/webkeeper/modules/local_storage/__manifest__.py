{
    "name": "Local Storage",
    "type": ["storage"],
    "entry_point": "local_storage::LocalStorage",
    "requires_setup": True,
    "description": "Saves archived media files to a folder on the local filesystem.",
    "version": "1.0.0",
    "configs": {
        "path_generator": {
            "default": "flat",
            "help": "Directory structure: 'flat' (root), 'url' (based on URL), 'random'",
            "choices": ["flat", "url", "random"],
        },
        "filename_generator": {
            "default": "static",
            "help": "Filename strategy: 'random' or 'static' (hash-based)",
            "choices": ["random", "static"],
        },
        "save_to": {
            "default": "./local_archive",
            "help": "Folder where archived content is saved",
        },
        "save_absolute": {
            "default": False,
            "type": "bool",
            "help": "Return absolute paths instead of relative",
        },
    },
    "dependencies": {},
}
