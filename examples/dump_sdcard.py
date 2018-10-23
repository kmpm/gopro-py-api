from goprocam import GoProCamera
import asyncio
import os
gpCam = GoProCamera.GoPro(working_path='./tmp')

@gpCam.on_log()
def log_handler(message, **kwargs):
    print(message)


async def run():
    """Downloads all of the SD card's contents and then formats the card.
    """
    await gpCam.downloadAll()
    await gpCam.delete("all")

    await gpCam.quit()

if not os.path.exists('./tmp'):
    os.makedirs('./tmp')

asyncio.get_event_loop().run_until_complete(run())
