{
    "name": "Console Database",
    "type": ["database"],
    "entry_point": "console_db::ConsoleDb",
    "requires_setup": False,
    "description": "Outputs archival status updates to the console using the logging system.",
    "version": "1.0.0",
    "configs": {},
    "dependencies": {
        "python": ["loguru"],
    },
}
