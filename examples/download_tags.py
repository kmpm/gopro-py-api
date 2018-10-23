from goprocam import GoProCamera, constants
import asyncio


gopro = GoProCamera.GoPro()


@gopro.on_log()
def log_handler(message, **kwargs):
    print('log>', message, kwargs)


async def run():
    # Downloads the video between 2 hilight tags
    last_media = await gopro.getMedia()
    if last_media.endswith(".MP4"):
        folder = await gopro.getMediaInfo("folder")
        file = await gopro.getMediaInfo("file")
        number_of_tags = await gopro.getVideoInfo("tag_count", folder, file)
        if number_of_tags != 0 and number_of_tags % 2 == 0:
            # Even number of tags
            tags = await gopro.getVideoInfo("tags", folder, file)
            status_id = await gopro.getClip(folder + "/" + file, constants.Clip.R720p, '1', str(tags[0]), str(tags[1]))  # constants.Clip.FPS_NORMAL
            url = await gopro.clipStatus(str(status_id))
            print('url', url)
            # while gopro.getClipURL(str(status_id)) is None:
            #     gopro.getClipURL(str(status_id))
            # print(gopro.getClipURL(str(status_id)))
            # gopro.downloadLastMedia(path=gopro.getClipURL(str(status_id)), custom_filename=gopro.getInfoFromURL(gopro.getClipURL(str(status_id)))[1])
            # print("Downloaded.")

    await gopro.quit()


asyncio.get_event_loop().run_until_complete(run())
