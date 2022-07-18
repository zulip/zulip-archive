from glob import iglob
from typing import Iterator

from xml_sitemap_writer import XMLSitemap


def build_sitemap(base_url: str, archive_dir_path: str, sitemap_write_dir_path: str):
    def iterate_html_files() -> Iterator[str]:
        # Iterator yields relative path like
        # archive/stream/10-errors/topic/laptop.html
        # TODO: Investigate when running in windows
        # TODO: Must ensure that the relative URLs are valid
        return iglob("**/*.html", root_dir=archive_dir_path, recursive=True)

    with XMLSitemap(sitemap_write_dir_path, base_url) as sitemap:
        sitemap.add_urls(iterate_html_files())
