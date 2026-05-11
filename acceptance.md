# Acceptance Criteria

## Task 1: Media and Metadata classes

### Media Acceptance Criteria
- [ ] Media created with filename="video.mp4" has media.filename == "video.mp4"
- [ ] Media with filename="video.mp4" has mimetype == "video/mp4"
- [ ] Media with filename="image.jpg" returns is_image() == True, is_video() == False
- [ ] Media.set("author", "John") returns self, Media.get("author") == "John"
- [ ] Media.add_url("http://cdn.com/file.mp4") adds URL to media.urls list
- [ ] Media with _key="my/path" has media.key == "my/path"
- [ ] Media with nested Media in properties yields them via all_inner_media()

### Metadata Acceptance Criteria
- [ ] Metadata() has default status == "no archiver"
- [ ] Metadata().set_url("https://example.com").get_url() == "https://example.com"
- [ ] Metadata.set_url("") raises AssertionError
- [ ] Metadata.set("title", "Test").get("title") == "Test"
- [ ] Metadata.success() changes is_success() to True
- [ ] Metadata.netloc property for "https://example.com/path" returns "example.com"
- [ ] Metadata.merge() combines two metadata objects, extending media lists
- [ ] Metadata.add_media() appends to media list, get_media_by_id() retrieves by id
- [ ] Metadata.set_timestamp() accepts datetime and string, get_timestamp() returns ISO string
- [ ] Metadata.is_empty() returns True for fresh metadata with only system fields
- [ ] Metadata.remove_duplicate_media_by_hash() deduplicates based on hash property
- [ ] Metadata.set_context/get_context() stores and retrieves context values separately from metadata
