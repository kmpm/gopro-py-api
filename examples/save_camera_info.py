import asyncio
import datetime
from os import path
from goprocam import GoProCamera
from goprocam.utils import dump_json

gpCam = GoProCamera.GoPro()


@gpCam.on_log()
def log_handler(message, **kwargs):
    print("{0}\t{1}".format(datetime.datetime.now(), message), kwargs.keys())
    if 'camera' in kwargs and 'data' in kwargs:
        data = kwargs.get('data')
        filename = "{0}.json".format(data["info"]["firmware_version"].replace(".", "_"))
        if path.exists('doc'):
            filename = path.join('doc', filename)
        dump_json(data, filename)
        print("Saved camera information to {0}".format(filename))


async def run():
    await gpCam.connect()
    await gpCam.quit()

asyncio.get_event_loop().run_until_complete(run())
