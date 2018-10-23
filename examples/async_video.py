from goprocam import GoProCamera
from goprocam import constants
import asyncio



gpCam = GoProCamera.GoPro()

async def run():
    print('Connecting')
    filename = 'something.MP4'

    await gpCam.connect()
    
    print('Setting things up')
    await asyncio.gather(gpCam.syncTime(),
        gpCam.video_settings("720p","120"),
        gpCam.gpControlSet(constants.Video.PROTUNE_VIDEO, constants.Video.ProTune.ON)
    )
    await gpCam.shutter(constants.start)
    await asyncio.sleep(10)
    await gpCam.shutter(constants.stop)
    await asyncio.sleep(2)
    await gpCam.downloadLastMedia(custom_filename=filename)

    await gpCam.quit()
    
@gpCam.on_connect()
def handle_connect(camera):
    print("Camera connected: {0}".format(camera))

@gpCam.on_control_set()
def handle_control_set(param, value, resp):
    print("Control Set: {0}={1} > {2}".format(param, value, resp))

@gpCam.on_control_command()
def handle_control_command(param, resp):
    print("Control Command: {0} > {1}".format(param, resp))

asyncio.get_event_loop().run_until_complete(run())