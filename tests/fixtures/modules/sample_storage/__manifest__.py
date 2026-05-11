{
    "name": "Sample Storage",
    "type": ["storage"],
    "entry_point": "sample_storage::SampleStorage",
    "requires_setup": False,
    "description": "A test storage module",
    "version": "1.0.0",
    "configs": {
        "path_generator": {"default": "flat"},
        "filename_generator": {"default": "random"}
    },
    "dependencies": {}
}
