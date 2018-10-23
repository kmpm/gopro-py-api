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
        print('number_of_tags', number_of_tags)
        if number_of_tags != 0 and number_of_tags % 2 == 0:
            # Even number of tags
            tags = await gopro.getVideoInfo("tags", folder, file)
            print('tags', tags)
            status_id = await gopro.getClip(folder + "/" + file, constants.Clip.R720p, '1', str(tags[0]), str(tags[1]))  # constants.Clip.FPS_NORMAL
            print('status_id', status_id)
            status = await gopro.clipStatus(status_id)
            print('status', status)
            url = await gopro.getClipURL(status_id)
            while url is None:
                asyncio.sleep(1)
                url = await gopro.getClipURL(status_id)
            print('url', url)
            gopro.downloadLastMedia(path=url, custom_filename=gopro.getInfoFromURL(url)[1])
            print("Downloaded.")
        else:
            await gopro.delete("all")

    await gopro.quit()


asyncio.get_event_loop().run_until_complete(run())
