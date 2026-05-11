{
    "name": "CLI Feeder",
    "type": ["feeder"],
    "entry_point": "cli_feeder::CLIFeeder",
    "requires_setup": True,
    "description": "Provides URLs directly from command line arguments to the archiving pipeline.",
    "version": "1.0.0",
    "configs": {
        "urls": {
            "default": None,
            "help": "URL(s) to archive, provided from command line",
        },
    },
    "dependencies": {},
}
