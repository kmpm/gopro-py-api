import asyncio
from goprocam import GoProCamera

gpCam = GoProCamera.GoPro()


@gpCam.on_log()
def log_handler(message, **kwargs):
    print('log>', message, kwargs)


async def run():
    await gpCam.connect()
    data = await gpCam.overview()

    print("camera overview")
    print("current mode: {0}".format(data.status.Mode))
    print("current submode: {0}".format(data.status.SubMode))
    print("current video resolution: {0}".format(data.settings.Resolution))
    print("current video framerate: {0}".format(data.settings.Framerate))
    print("pictures taken: {0}".format(data.status.PhotosTaken))
    print("videos taken: {0}".format(data.status.VideosTaken))
    print("videos left: {0}".format(data.status.RemVideoTime))
    print("pictures left: {0}".format(data.status.RemPhotos))
    print("battery left: {0}".format(data.status.BatteryLevel))
    print("space left in sd card: {0}".format(data.status.RemainingSpace))
    print("camera SSID: {0}".format(data.status.CamName))
    print("Is Busy: {0}".format(data.status.IsBusy))
    print("Clients connected: {0}".format(data.status.IsConnected))
    # print("camera model: {0}".format() + "" + self.infoCamera(constants.Camera.Name))
    # print("firmware version: " + "" + self.infoCamera(constants.Camera.Firmware))
    # print("serial number: " + "" + self.infoCamera(constants.Camera.SerialNumber))

    print("\n--media--")
    print(await gpCam.listMedia(True))

    await gpCam.quit()

asyncio.get_event_loop().run_until_complete(run())
