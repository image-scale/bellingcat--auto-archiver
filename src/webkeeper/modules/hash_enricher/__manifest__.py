{
    "name": "Hash Enricher",
    "type": ["enricher"],
    "entry_point": "hash_enricher::HashEnricher",
    "requires_setup": False,
    "description": "Calculates cryptographic hashes for media files to ensure integrity and authenticity.",
    "version": "1.0.0",
    "configs": {
        "algorithm": {
            "default": "SHA-256",
            "help": "Hash algorithm to use",
            "choices": ["SHA-256", "SHA3-512"],
        },
        "chunksize": {
            "default": 16000000,
            "help": "Bytes to read at a time (default 16MB)",
            "type": "int",
        },
    },
    "dependencies": {},
}
