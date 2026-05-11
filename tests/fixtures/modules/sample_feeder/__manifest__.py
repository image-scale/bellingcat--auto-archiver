{
    "name": "Sample Feeder",
    "type": ["feeder"],
    "entry_point": "sample_feeder::SampleFeeder",
    "requires_setup": False,
    "description": "A test feeder module",
    "version": "1.0.0",
    "configs": {
        "source": {
            "default": "cli",
            "help": "Source of URLs"
        },
        "max_items": {
            "default": 100,
            "help": "Maximum items to process",
            "type": "int"
        }
    },
    "dependencies": {}
}
