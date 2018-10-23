import sys
import unittest
import asyncio

from goprocam import GoProCamera
from goprocam import constants

def _run(coro):
    """Run the given coroutine."""
    return asyncio.get_event_loop().run_until_complete(coro)

class TestGoPro(unittest.TestCase):
    gpCam = None

    def setUp(self):
        self.gpCam = GoProCamera.GoPro()

    def tearDown(self):
        if self.gpCam:
            self.gpCam.quit()
            self.gpCam = None

    def test_connect(self):
        _run(self.gpCam.connect())
        