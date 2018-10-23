import unittest
import asyncio

from goprocam import GoProCamera
from goprocam import constants


def _run(coro):
    """Run the given coroutine."""
    return asyncio.get_event_loop().run_until_complete(coro)


async def _cleanup(gpCam):
    await gpCam.delete("all")
    await gpCam.quit()


class TestGoPro(unittest.TestCase):
    gpCam = None

    def setUp(self):
        self.gpCam = GoProCamera.GoPro()

    def tearDown(self):
        _run(_cleanup(self.gpCam))
        self.gpCam = None

    def test_connect(self):
        _run(self.gpCam.connect())
        self.assertEqual(self.gpCam.camera.model, "HERO4 Black")

    def test_5sec_video_shutter(self):
        async def work(gpCam):
            await asyncio.gather(
                gpCam.syncTime(),
                gpCam.video_settings("720p", "120"),
                gpCam.gpControlSet(constants.Video.PROTUNE_VIDEO, constants.Video.ProTune.ON)
            )
            await gpCam.shutter(constants.start)
            await asyncio.sleep(5)
            await gpCam.shutter(constants.stop)
        _run(work(self.gpCam))

    def test_5sec_video(self):
        async def work(gpCam):
            await asyncio.gather(
                gpCam.syncTime(),
                gpCam.video_settings("720p", "120"),
                gpCam.gpControlSet(constants.Video.PROTUNE_VIDEO, constants.Video.ProTune.ON)
            )
            media = await gpCam.shoot_video(5)
            # http://10.5.5.9:8080/videos/DCIM/100GOPRO/GOPR0849.MP4
            self.assertRegex(media, r'^http://10\.5\.5\.9:8080/videos/DCIM/100GOPRO/GOPR[0-9].*\.MP4')

        _run(work(self.gpCam))
