from goprocam import GoProCamera, constants
import asyncio

gpCam = GoProCamera.GoPro()
videos_duration = [10, 30]


async def run():
    await gpCam.connect()
    await gpCam.video_settings("720p", "50")
    await gpCam.gpControlSet(constants.Video.PROTUNE_VIDEO, constants.Video.ProTune.ON)
    for i in videos_duration:
        print("Recording and downloading " + str(i) + " seconds video")
        await gpCam.downloadLastMedia(await gpCam.shoot_video(i), custom_filename="VIDEO_{0}.MP4".format(i))
        await asyncio.sleep(2)

    await gpCam.quit()


asyncio.get_event_loop().run_until_complete(run())
