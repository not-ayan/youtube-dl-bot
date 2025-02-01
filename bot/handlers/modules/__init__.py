from aiogram import Router

from . import tiktok, youtube, instagram, pinterest, rx_gallery
# from . import x, reddit

router = Router()
router.include_router(youtube.router)
router.include_router(tiktok.router)
# router.include_router(x.router)
router.include_router(instagram.router)
# router.include_router(reddit.router)
router.include_router(pinterest.router)
router.include_router(rx_gallery.router)
