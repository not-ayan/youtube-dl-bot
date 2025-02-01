import os
import glob
from typing import List
from handlers.modules.master import BaseScrapper, MediaType, shell, take_ss, get_type

class GalleryDL(BaseScrapper):
    async def scrape(self):
        os.makedirs(self.media_download_dir)

        await shell.run_shell_cmd(
            cmd=f"gallery-dl -q --range '0-4' -D {self.media_download_dir} '{self.original_url}'",
            timeout=15,
            ret_val=0,
        )

        files_list: List[str] = glob.glob(f"{self.media_download_dir}/*")

        if not files_list:
            self.clean_downloads()
            return

        self.extraction_success = True

        if len(files_list) > 1:
            self.grouped_media = files_list
            self.media_type: MediaType = MediaType.GROUP

            for file in files_list:
                if get_type(path=file) in self.TO_SS_TYPES:
                    self.grouped_media_thumbs[file] = await take_ss(
                        video=file, path=self.media_download_dir
                    )

        else:
            self.media_type: MediaType = get_type(path=files_list[0])
            self.single_media = files_list[0]

            if self.media_type in self.TO_SS_TYPES:
                self.single_media_thumb = await take_ss(
                    video=self.single_media, path=self.media_download_dir
                )
