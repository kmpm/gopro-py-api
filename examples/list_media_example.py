from goprocam import GoProCamera, constants
import asyncio

# hero3
gpCam = GoProCamera.GoPro(constants.auth)


@gpCam.on_log()
def log_handler(message, **kwargs):
    print(message)


async def run():
    await gpCam.overview()
    await gpCam.listMedia(True)

asyncio.get_event_loop().run_until_complete(run())
