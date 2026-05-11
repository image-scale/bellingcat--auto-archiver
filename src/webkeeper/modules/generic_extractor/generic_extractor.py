"""Generic extractor module using yt-dlp to download media."""

import os
from typing import Generator

import yt_dlp
from loguru import logger

from webkeeper.core import Extractor, Metadata, Media


class GenericExtractor(Extractor):
    """Extractor that uses yt-dlp to download media from various platforms."""

    def suitable_extractors(self, url: str) -> Generator:
        """Yield extractors that can handle this URL."""
        for extractor in yt_dlp.YoutubeDL()._ies.values():
            if not extractor.working():
                continue
            if extractor.suitable(url):
                yield extractor

    def suitable(self, url: str) -> bool:
        """Check if any yt-dlp extractor can handle this URL."""
        return any(self.suitable_extractors(url))

    def download(self, item: Metadata) -> Metadata:
        """Download media from the URL using yt-dlp."""
        url = item.get_url()

        ydl_options = {
            "outtmpl": os.path.join(self.tmp_dir or "/tmp", "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "noplaylist": not getattr(self, "allow_playlist", False),
            "writesubtitles": getattr(self, "subtitles", True),
            "writeautomaticsub": getattr(self, "subtitles", True),
        }

        proxy = getattr(self, "proxy", "")
        if proxy:
            ydl_options["proxy"] = proxy

        max_dl = getattr(self, "max_downloads", "inf")
        if max_dl != "inf":
            ydl_options["max_downloads"] = int(max_dl)

        try:
            with yt_dlp.YoutubeDL(ydl_options) as ydl:
                info = ydl.extract_info(url, download=True)

                if not info:
                    return False

                result = Metadata().set_url(url)

                if info.get("is_live", False) and not getattr(self, "livestreams", False):
                    logger.warning("Skipping livestream")
                    return False

                entries = info.get("entries", [info])
                for entry in entries:
                    if not entry:
                        continue

                    filename = ydl.prepare_filename(entry)
                    if os.path.exists(filename):
                        media = Media(filename=filename)
                        if entry.get("duration"):
                            media.set("duration", entry["duration"])
                        if entry.get("title"):
                            media.set("title", entry["title"])
                        result.add_media(media)

                if result.get_title() is None and info.get("title"):
                    result.set_title(info["title"])

                if info.get("description"):
                    result.set_content(info["description"])

                if info.get("thumbnail"):
                    try:
                        thumb_path = self.download_from_url(info["thumbnail"])
                        if thumb_path:
                            result.add_media(Media(filename=thumb_path), id="cover")
                    except Exception as e:
                        logger.debug(f"Could not download thumbnail: {e}")

                if not result.media:
                    return False

                result.success("yt-dlp")
                return result

        except yt_dlp.utils.DownloadError as e:
            logger.warning(f"yt-dlp download error: {e}")
            return False
        except Exception as e:
            logger.error(f"Generic extractor error: {e}")
            return False
