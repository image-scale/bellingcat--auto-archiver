{
    "name": "Generic Extractor",
    "type": ["extractor"],
    "entry_point": "generic_extractor::GenericExtractor",
    "requires_setup": False,
    "description": "Downloads media from video platforms using yt-dlp.",
    "version": "1.0.0",
    "configs": {
        "subtitles": {
            "default": True,
            "help": "Download subtitles if available",
            "type": "bool",
        },
        "comments": {
            "default": False,
            "help": "Download comments if available",
            "type": "bool",
        },
        "livestreams": {
            "default": False,
            "help": "Download live streams",
            "type": "bool",
        },
        "allow_playlist": {
            "default": False,
            "help": "Allow downloading playlists",
            "type": "bool",
        },
        "max_downloads": {
            "default": "inf",
            "help": "Maximum number of videos to download",
        },
        "proxy": {
            "default": "",
            "help": "HTTP/HTTPS proxy to use",
        },
    },
    "dependencies": {
        "python": ["yt_dlp"],
        "bin": ["ffmpeg"],
    },
}
