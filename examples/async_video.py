from goprocam import GoProCamera, constants
import asyncio

gpCam = GoProCamera.GoPro()


async def run():
    print('Connecting')
    filename = 'something.MP4'

    await gpCam.connect()

    print('Setting things up')
    await asyncio.gather(
        gpCam.syncTime(),
        gpCam.mode(constants.Mode.PhotoMode),
        gpCam.video_settings("720p", "120"),
        gpCam.gpControlSet(constants.Video.PROTUNE_VIDEO, constants.Video.ProTune.ON)
    )
    print('shoot_vieo', await gpCam.shoot_video(0))
    await asyncio.sleep(10)
    await gpCam.shutter(constants.stop)
    await asyncio.sleep(2)
    await gpCam.downloadLastMedia(custom_filename=filename)
    print("done")
    await gpCam.quit()


@gpCam.on_connect()
def handle_connect(camera):
    print("Camera connected: {0}".format(camera))


@gpCam.on_log()
def handle_log(message, **kwargs):
    print("log", message, kwargs)


asyncio.get_event_loop().run_until_complete(run())
