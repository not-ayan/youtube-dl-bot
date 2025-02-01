import os
import glob
import logging
from abc import ABC, abstractmethod

class BaseScrapper(ABC):
    def __init__(self, original_url: str, media_download_dir: str):
        self.original_url = original_url
        self.media_download_dir = media_download_dir
        self.extraction_success = False
        self.grouped_media = []
        self.grouped_media_thumbs = {}
        self.single_media = ""
        self.single_media_thumb = ""
        self.media_type = None

    @abstractmethod
    async def scrape(self):
        pass

    def clean_downloads(self):
        if os.path.isdir(self.media_download_dir):
            import shutil
            shutil.rmtree(self.media_download_dir)
