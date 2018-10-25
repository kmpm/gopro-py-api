import asyncio
import datetime
from goprocam import GoProCamera, constants

gpCam = GoProCamera.GoPro()


async def run():
    print('Connecting')

    await gpCam.connect()

    print('Setting things up')
    await asyncio.gather(
        gpCam.syncTime(),
        gpCam.video_settings("720p", "200"),
        gpCam.gpControlSet(constants.Video.PROTUNE_VIDEO, constants.Video.ProTune.ON)
    )
    print('shoot_video=', await gpCam.shoot_video(5))
    await asyncio.sleep(2)
    await gpCam.downloadLastMedia()
    print("done")
    await gpCam.quit()


@gpCam.on_connect()
def handle_connect(camera):
    print("Camera connected: {0}".format(camera))


@gpCam.on_log()
def handle_log(message, **kwargs):
    print("{0}\t{1}".format(datetime.datetime.now(), message), kwargs.keys())


asyncio.get_event_loop().run_until_complete(run())
