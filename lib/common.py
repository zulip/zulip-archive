import os


def exit_immediately(s):
    print("\nERROR\n", s)
    exit(1)


# Safely open dir/filename, creating dir if it doesn't exist
def open_outfile(dir, filename, mode):
    if not dir.exists():
        os.makedirs(str(dir))
    return (dir / filename).open(mode, encoding="utf-8")


def stream_validator(settings):
    if not hasattr(settings, "included_streams"):
        exit_immediately("Please set included_streams.")

    if len(settings.included_streams) == 0:
        exit_immediately('Please add "*" to included_streams.')

    if hasattr(settings, "excluded_streams"):
        excluded_streams = set(settings.excluded_streams)
    else:
        excluded_streams = set()

    included_streams = set(settings.included_streams)

    def validator(stream):
        stream_name = stream["name"]
        is_web_public = stream["is_web_public"]
        is_public = not stream["invite_only"]

        if stream_name in excluded_streams:
            return False

        if "web-public:*" in included_streams and is_web_public:
            return True

        # The bare * case is for backwards-compatibility.
        if ("*" in included_streams or "public:*" in included_streams) and is_public:
            return True

        return stream_name in included_streams

    return validator
