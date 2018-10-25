#
import time
import socket
import urllib.request
import json
import re
from goprocam import constants
import datetime
import struct
import subprocess
from socket import timeout
from urllib.error import HTTPError
from urllib.error import URLError
import math
import base64
import sys
import ssl

import asyncio
from goprocam.clients import AsyncClient
from goprocam.utils import media_size, deprecated, Struct, reconstruct_status, Parsers
from goprocam.errors import CameraIdentificationError, GoProError, UnsupportedCameraError


class CameraInfo:
    firmware_version = None
    apitype = None

    def __init__(self, model, model_type, apitype='gpcontrol', **kwargs):
        self.model = model
        self.apitype = apitype
        self.model_type = model_type
        info = kwargs.pop('info', None)
        if info:
            for key in info:
                setattr(self, key, info[key])

        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self):
        msg = "{0}".format(self.model)
        if self.apitype:
            msg += ", api:{0}".format(self.apitype)
        if self.firmware_version:
            msg += ", fw:{0}".format(self.firmware_version)
        return msg


class MediaInfo:
    def __init__(self, folder, name, size):
        self.folder = folder
        self.name = name
        self.size = size

    @property
    def size_readable(self):
        return media_size(self.size)

    def __str__(self):
        return "<MediaInfo folder:{0}, name:{1}, size:{2}>".format(self.folder, self.name, self.size)


class GoPro:
    async def prepare_gpcontrol(self):
        try:
            jsondata = await self._client.getJSON('http://' + self.ip_addr + '/gp/gpControl', timeout=5)
            response = jsondata["info"]["firmware_version"]
            if "HX" in response:  # Only session cameras.
                connectedStatus = False
                while connectedStatus is False:
                    json_data = await self._client.getJSON("http://" + self.ip_addr + "/gp/gpControl/status")
                    # print(json_data["status"]["31"])
                    if json_data["status"]["31"] >= 1:
                        connectedStatus = True
        except (HTTPError, URLError) as error:
            await self.prepare_gpcontrol()
        except timeout:
            await self.prepare_gpcontrol()

        # print("Camera successfully connected!")

    def __init__(self, ip_address="10.5.5.9", mac_address="AA:BB:CC:DD:EE:FF", working_path='./'):
        if sys.version_info[0] < 3:
            raise Exception("Needs Python v3, run again on a virtualenv or install Python 3")
        self.ip_addr = ip_address
        self._camera = ""
        self._connect_handler = None  # type: Optional[Callable]
        self._control_set_handler = None
        self._control_command_handler = None
        self._send_camera_handler = None
        self._log_handler = None
        self._client = AsyncClient(working_path=working_path)

        try:
            from getmac import get_mac_address
            self._mac_address = get_mac_address(ip="10.5.5.9")
        except ImportError:
            self._mac_address = mac_address

    def __str__(self):
        return str(self.infoCamera())

    async def _sleep(self, period):
        if period > 2:
            self._handle_log("sleeping for {0} seconds".format(period))
        return await asyncio.sleep(period)

    def KeepAlive(self):
        while True:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto("_GPHD_:0:0:2:0.000000\n".encode(), (self.ip_addr, 8554))
            time.sleep(2500 / 1000)

    def getPassword(self):
        try:
            PASSWORD = urllib.request.urlopen('http://' + self.ip_addr + '/bacpac/sd', timeout=5).read()
            password = str(PASSWORD, 'utf-8')
            password_parsed = re.sub(r'\W+', '', password)
            return password_parsed
        except (HTTPError, URLError) as error:
            return ""
            print("Error code:" + str(error.code) + "\nMake sure the connection to the WiFi camera is still active.")
        except timeout:
            return ""
            print("HTTP Timeout\nMake sure the connection to the WiFi camera is still active.")

    async def gpControlSet(self, param, value):
        # sends Parameter and value to gpControl/setting

        if self._camera and self._camera.model_type in ['HD7']:
            # unsupported for above
            if param in [constants.Video.PROTUNE_VIDEO]:
                return
        try:
            resp = await self._client.getText(
                'http://' + self.ip_addr + '/gp/gpControl/setting/' + param + '/' + value, timeout=5
            )
            self._handle_log("gpControlSet({0},{1}) > {2}".format(param, value, resp))
            return resp
        except (HTTPError, URLError) as error:
            return ""
            print("Error code:" + str(error.code) + "\nMake sure the connection to the WiFi camera is still active.")
        except timeout:
            return ""
            print("HTTP Timeout\nMake sure the connection to the WiFi camera is still active.")

    async def gpControlCommand(self, param):
        """Sends a gpControl/command to camera and returns JSON respons if parsable
        """
        try:
            resp = await self._client.getText('http://' + self.ip_addr + '/gp/gpControl/command/' + param, timeout=5)

            # replace single backslash with forwardslash to fix bad json format
            resp = json.loads(resp.replace("\\", "/"))
            self._handle_log("gpControlCommand({0}) > {1}".format(param, resp))
            return resp
        except (HTTPError, URLError) as error:
            return ""
            print("Error code:" + str(error.code) + "\nMake sure the connection to the WiFi camera is still active.")
        except timeout:
            return ""
            print("HTTP Timeout\nMake sure the connection to the WiFi camera is still active.")

    async def gpControlExecute(self, param):
        try:
            resp = await self._client.getText('http://' + self.ip_addr + '/gp/gpControl/execute?' + param, timeout=5)
            # TODO: on_ handler
            return resp
        except (HTTPError, URLError) as error:
            return ""
            print("Error code:" + str(error.code) + "\nMake sure the connection to the WiFi camera is still active.")
        except timeout:
            return ""
            print("HTTP Timeout\nMake sure the connection to the WiFi camera is still active.")

    async def sendCamera(self, param, value=""):
        value_notempty = ""
        if not value == "":
            value_notempty = str('&p=%' + value)
        # sends parameter and value to /camera/
        try:
            resp = await self._client.getText(
                'http://' + self.ip_addr + '/camera/' + param + '?t=' +
                self.getPassword() + value_notempty, timeout=5
            )
            self._handle_log("sendCamera({0}, {1}) > {2}".format(param, value, resp))
            return resp
        except (HTTPError, URLError) as error:
            print("Error code:" + str(error.code) + "\nMake sure the connection to the WiFi camera is still active.")
        except timeout:
            print("HTTP Timeout\nMake sure the connection to the WiFi camera is still active.")

    @deprecated
    async def sendBacpac(self, param, value):
        # sends parameter and value to /bacpac/
        value_notempty = ""
        if value:
            value_notempty = str('&p=%' + value)
        try:
            await self._client.getText(
                'http://' + self.ip_addr + '/bacpac/' + param + '?t=' + self.getPassword() +
                value_notempty, timeout=5)
        except (HTTPError, URLError) as error:
            print("Error code:" + str(error.code) + "\nMake sure the connection to the WiFi camera is still active.")
        except timeout:
            print("HTTP Timeout\nMake sure the connection to the WiFi camera is still active.")

    async def is_apitype(self, apitype):
        return (await self.whichCam()).apitype == apitype

    async def whichCam(self):
        # This returns what type of camera is currently connected.
        # gpcontrol: HERO4 Black and Silver, HERO5 Black and Session,
        #   HERO Session (formally known as HERO4 Session), HERO+ LCD, HERO+.
        # auth: HERO2 with WiFi BacPac, HERO3 Black/Silver/White, HERO3+ Black and Silver.
        if self._camera:
            return self._camera
        else:
            found = False
            jsondata = {}
            try:
                jsondata = await self._client.getJSON('http://' + self.ip_addr + '/gp/gpControl', timeout=5)
                response = jsondata["info"]["firmware_version"]
                response_parsed = 3
                exception_found = False
                model_type = ''
                apitype = 'gpcontrol'
                if "HD" in response:
                    model_type = response.split('.')[0]
                    response_parsed = response.split("HD")[1][0]

                exceptions = ["HX", "FS", "H18"]
                for camera in exceptions:
                    if camera in response:
                        exception_found = True
                        model_type = camera
                        break

                # HD4 (Hero4), HD5 (Hero5), HD6 (Hero6)...
                # Exceptions: HX (HeroSession), FS (Fusion), H18 (Hero 2018)
                if int(response_parsed) > 3 or exception_found:
                    # print(jsondata["info"]["model_name"] + "\n" + jsondata["info"]["firmware_version"])
                    await self.prepare_gpcontrol()
                    self._camera = CameraInfo(jsondata["info"]["model_name"], model_type, apitype,
                                              info=jsondata["info"])
                    found = True
                else:
                    raise CameraIdentificationError('Unsupported camera:' + response, 400)

            except Exception as err:
                raise CameraIdentificationError('Error identifying camera or no camera connected', 500, err)

            if found:
                self._handle_log("detected camera ".format(self._camera.model), camera=self._camera, data=jsondata)
                return self._camera

    async def getStatus(self, param=None, value=None):
        if (await self.is_apitype("gpcontrol")):
            try:
                json_data = await self._client.getJSON("http://" + self.ip_addr + "/gp/gpControl/status", timeout=5)

                if param and value:
                    return json_data[param][value]
                struct = reconstruct_status(json_data)
                return struct
            except (HTTPError, URLError) as error:
                return ""
                print("Error code:" + str(error.code) +
                      "\nMake sure the connection to the WiFi camera is still active.")
            except timeout:
                return ""
                print("HTTP Timeout\nMake sure the connection to the WiFi camera is still active.")
        else:
            response = await self._client.getText("http://" + self.ip_addr + "/camera/sx?t=" + self.getPassword(),
                                                  timeout=5)
            response_hex = str(bytes.decode(base64.b16encode(response), 'utf-8'))
            return str(response_hex[param[0]:param[1]])

    async def getStatusRaw(self):
        if (await self.is_apitype("gpcontrol")):
            try:
                return self._client.getText("http://" + self.ip_addr + "/gp/gpControl/status", timeout=5)
            except (HTTPError, URLError) as error:
                return ""
                print("Error code:" + str(error.code) +
                      "\nMake sure the connection to the WiFi camera is still active.")
            except timeout:
                return ""
                print("HTTP Timeout\nMake sure the connection to the WiFi camera is still active.")
        elif (await self.is_apitype("auth")):
            try:
                return await self._client.getText("http://" + self.ip_addr + "/camera/sx?t=" + self.getPassword(),
                                                  timeout=5)
            except (HTTPError, URLError) as error:
                return ""
                print("Error code:" + str(error.code) +
                      "\nMake sure the connection to the WiFi camera is still active.")
            except timeout:
                return ""
                print("HTTP Timeout\nMake sure the connection to the WiFi camera is still active.")
        else:
            print("Error, camera not defined.")

    async def changeWiFiSettings(self, ssid, password):
        if (await self.is_apitype("gpcontrol")):
            await self.gpControlCommand("wireless/ap/ssid?ssid=" + ssid + "&pw=" + password)
            return True

    async def infoCamera(self, option=""):
        if (await self.is_apitype("gpcontrol")):
            try:
                parse_read = await self._client.getJSON('http://' + self.ip_addr + '/gp/gpControl', timeout=5)
                parsed_info = ""
                if option == "":
                    parsed_info = parse_read["info"]
                else:
                    parsed_info = parse_read["info"][option]
                return parsed_info
            except (HTTPError, URLError) as error:
                return ""
                print("Error code:" + str(error.code) +
                      "\nMake sure the connection to the WiFi camera is still active.")
            except timeout:
                return ""
                print("HTTP Timeout\nMake sure the connection to the WiFi camera is still active.")
        elif (await self.is_apitype("auth")):
            if option == "model_name" or option == "firmware_version":
                try:
                    data = await self._client.getText('http://' + self.ip_addr + '/camera/cv', timeout=5)
                    parsed = re.sub(r'\W+', '', str(data))
                    print(parsed)
                    return parsed  # an error is raised in take_photo if no value is returned
                except (HTTPError, URLError) as error:
                    return ""
                    print("Error code:" + str(error.code) +
                          "\nMake sure the connection to the WiFi camera is still active.")
                except timeout:
                    return ""
                    print("HTTP Timeout\nMake sure the connection to the WiFi camera is still active.")
            if option == "ssid":
                try:
                    data = await self._client.getText('http://' + self.ip_addr + '/bacpac/cv', timeout=5)
                    parsed = re.sub(r'\W+', '', str(data))
                    print(parsed)
                    return parsed  # an error is raised in take_photo if no value is returned
                except (HTTPError, URLError) as error:
                    return ""
                    print("Error code:" + str(error.code) +
                          "\nMake sure the connection to the WiFi camera is still active.")
                except timeout:
                    return ""
                    print("HTTP Timeout\nMake sure the connection to the WiFi camera is still active.")
        else:
            print("Error, camera not defined.")

    async def shutter(self, param):
        if (await self.is_apitype("gpcontrol")):
            return await self.gpControlCommand("shutter?p=" + param)
        else:
            if len(param) == 1:
                param = "0" + param
            return await self.sendBacpac("SH", param)

    async def mode(self, mode, submode="0"):
        """sets camera mode + optional submode
        """
        result = None
        if (await self.is_apitype("gpcontrol")):
            result = await self.gpControlCommand("sub_mode?mode=" + mode + "&sub_mode=" + submode)
        else:
            if len(mode) == 1:
                mode = "0" + mode
            result = await self.sendCamera("CM", mode)
        self._handle_log("mode={0}, submode={1}: result={2}".format(mode, submode, result))
        return result

    async def delete(self, option):
        if (await self.is_apitype("gpcontrol")):
            if isinstance(option, int):
                # This allows you to delete x number of files backwards.
                # Will delete a timelapse/burst entirely as its interpreted as a single file.
                tasks = []
                for _ in range(option):
                    tasks.append(self.gpControlCommand("storage/delete/" + "last"))
                return await asyncio.gather(tasks)
            else:
                return await self.gpControlCommand("storage/delete/" + option)
        else:
            if isinstance(option, int):
                tasks = []
                for _ in range(option):
                    tasks.append(self.sendCamera("DL"))
                return await asyncio.gather(tasks)
            else:
                if option == "last":
                    return await self.sendCamera("DL")
                if option == "all":
                    return await self.sendCamera("DA")

    def deleteFile(self, folder, file):
        if folder.startswith("http://" + self.ip_addr):
            self.getInfoFromURL(folder)
            if self.whichCam() == "gpcontrol":
                print(self.gpControlCommand("storage/delete?p=" + self.getInfoFromURL(folder)[0] + "/" +
                                            self.getInfoFromURL(folder)[1]))
            else:
                print(self.sendCamera("DA", self.getInfoFromURL(folder)[0] + "/" + self.getInfoFromURL(folder)[1]))
        else:
            if self.whichCam() == "gpcontrol":
                print(self.gpControlCommand("storage/delete?p=" + folder + "/" + file))
            else:
                print(self.sendCamera("DA", folder + "/" + file))

    def locate(self, param):
        if self.whichCam() == "gpcontrol":
            print(self.gpControlCommand("system/locate?p=" + param))
        else:
            print(self.sendCamera("LL", "0" + param))

    def hilight(self):
        if self.whichCam() == "gpcontrol":
            print(self.gpControlCommand("storage/tag_moment"))
        else:
            print("Not supported.")

    def power_off(self):
        if self.whichCam() == "gpcontrol":
            print(self.gpControlCommand("system/sleep"))
        else:
            print(self.sendBacpac("PW", "00"))

    def power_on(self, _mac_address=""):
        print("Waking up...")
        mac_address = _mac_address
        if mac_address is None:
            mac_address = "AA:BB:CC:DD:EE:FF"
        else:
            mac_address = str(mac_address)
            if len(mac_address) == 12:
                pass
            elif len(mac_address) == 17:
                sep = mac_address[2]
                mac_address = mac_address.replace(sep, '')

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        data = bytes('FFFFFFFFFFFF' + mac_address * 16, 'utf-8')
        message = b''
        for i in range(0, len(data), 2):
                message += struct.pack(b'B', int(data[i: i + 2], 16))
        sock.sendto(message, (self.ip_addr, 9))
        # Fallback for HERO5
        sock.sendto(message, (self.ip_addr, 7))

    async def pair(self, usepin=True):
        raise NotImplementedError('pairing is not implemented')
        # This is a pairing procedure needed for HERO4 and HERO5 cameras.
        # When those type GoPro camera are purchased the GoPro Mobile app needs an
        # authentication code when pairing the camera to a mobile device for the first time.
        # The code is useless afterwards. This function will pair your GoPro to the machine
        # without the need of using the mobile app -- at all.
        if usepin is False:
            paired_resp = ""
            while "{}" not in paired_resp:
                paired_resp = await self._client.getText(
                    'http://' + self.ip_addr + '/gp/gpControl/command/wireless/pair/complete?success = 1&deviceName=' +
                    socket.gethostname(), timeout=5)
            return True
        else:
            print(
                "Make sure your GoPro camera is in pairing mode!\n",
                "Go to settings > Wifi > PAIR > GoProApp to start pairing.\n",
                "Then connect to it, the ssid name should be \n",
                "GOPRO-XXXX/GPXXXXX/GOPRO-BP-XXXX and the password is goprohero")

            code = str(input("Enter pairing code: "))
            _context = ssl._create_unverified_context()
            ssl._create_default_https_context = ssl._create_unverified_context
            response_raw = urllib.request.urlopen(
                'https://' + self.ip_addr + '/gpPair?c = start&pin=' + code + '&mode = 0', context=_context
            ).read().decode('utf8')
            print(response_raw)
            response_raw = urllib.request.urlopen(
                'https://' + self.ip_addr + '/gpPair?c = finish&pin=' + code + '&mode = 0', context=_context
            ).read().decode('utf8')
            print(response_raw)
            wifi_ssid = input("Enter your desired camera wifi ssid name: ")
            wifi_pass = input("Enter new wifi password: ")
            self.gpControlCommand("wireless/ap/ssid?ssid=" + wifi_ssid + "&pw=" + wifi_pass)
            print("Connect now!")

    async def power_on_auth(self):
        return await self.sendBacpac("PW", "01")

    async def video_settings(self, res, fps="none"):
        cam = await self.whichCam()
        if cam == "gpcontrol":
            x = "constants.Video.Resolution.R" + res
            videoRes = eval(x, {}, {"constants": constants})
            await self.gpControlSet(constants.Video.RESOLUTION, videoRes)
            if fps != "none":
                x = "constants.Video.FrameRate.FR" + fps
                videoFps = eval(x, {}, {"constants": constants})
                await self.gpControlSet(constants.Video.FRAME_RATE, videoFps)
        elif cam == "auth":
            if res == "4k":
                await self.sendCamera(constants.Hero3Commands.VIDEO_RESOLUTION, "06")
            elif res == "4K_Widescreen":
                await self.sendCamera(constants.Hero3Commands.VIDEO_RESOLUTION, "08")
            elif res == "2kCin":
                await self.sendCamera(constants.Hero3Commands.VIDEO_RESOLUTION, "07")
            elif res == "2_7k":
                await self.sendCamera(constants.Hero3Commands.VIDEO_RESOLUTION, "05")
            elif res == "1440p":
                await self.sendCamera(constants.Hero3Commands.VIDEO_RESOLUTION, "04")
            elif res == "1080p":
                await self.sendCamera(constants.Hero3Commands.VIDEO_RESOLUTION, "03")
            elif res == "960p":
                await self.sendCamera(constants.Hero3Commands.VIDEO_RESOLUTION, "02")
            elif res == "720p":
                await self.sendCamera(constants.Hero3Commands.VIDEO_RESOLUTION, "01")
            elif res == "480p":
                await self.sendCamera(constants.Hero3Commands.VIDEO_RESOLUTION, "00")
            if fps != "none":
                x = "constants.Hero3Commands.FrameRate.FPS" + fps
                videoFps = eval(x)
                await self.sendCamera(constants.Hero3Commands.FRAME_RATE, videoFps)

    async def take_photo(self, timer=1):
        info = await self.infoCamera(constants.Camera.Name)
        if "HERO5 Black" in info or "HERO6" in info:
            await self.mode(constants.Mode.PhotoMode, constants.Mode.SubMode.Photo.Single_H5)
        else:
            await self.mode(constants.Mode.PhotoMode)
        if timer > 0:
            self._sleep(timer)

        await self.shutter(constants.start)

        if (await self.is_apitype("gpcontrol")):
            ready = int(await self.getStatus(constants.Status.Status, constants.Status.STATUS.IsBusy))
            while ready == 1:
                    ready = int(await self.getStatus(constants.Status.Status, constants.Status.STATUS.IsBusy))
            return await self.getMedia()
        elif (await self.is_apitype("auth")):
            raise UnsupportedCameraError()

    async def shoot_video(self, duration=0):
        await self.mode(constants.Mode.VideoMode)
        await self._sleep(1)  # some time to change mode
        await self.shutter(constants.start)

        if duration != 0 and duration > 2:
            await self._sleep(duration)
            await self.shutter(constants.stop)
            if (await self.is_apitype("gpcontrol")):
                ready = int(await self.getStatus(constants.Status.Status, constants.Status.STATUS.IsBusy))
                while ready == 1:
                    ready = int(await self.getStatus(constants.Status.Status, constants.Status.STATUS.IsBusy))
                return await self.getMedia()
            elif (await self.is_apitype("auth")):
                raise UnsupportedCameraError

    async def syncTime(self):
        now = datetime.datetime.now()
        year = str(now.year)[-2:]
        datestr_year = format(int(year), 'x')
        datestr_month = format(now.month, 'x')
        datestr_day = format(now.day, 'x')
        datestr_hour = format(now.hour, 'x')
        datestr_min = format(now.minute, 'x')
        datestr_sec = format(now.second, 'x')
        datestr = str(
            "%" + str(datestr_year) + "%" + str(datestr_month) + "%" +
            str(datestr_day) + "%" + str(datestr_hour) + "%" +
            str(datestr_min) + "%" + str(datestr_sec))
        cam = await self.whichCam()
        if cam == "gpcontrol":
            try:
                res = await self.gpControlCommand('setup/date_time?p=' + datestr)
            except GoProError as err:
                self._handle_log("Error {0} syncing time".format(err.error_code), err=err)
                res = None
        else:
            res = await self.sendCamera("TM", datestr)
        return res

    async def reset(self, r):
        return await self.gpControlCommand(r + "/protune/reset")

    async def setZoom(self, zoomLevel):
        if zoomLevel >= 0 and zoomLevel <= 100:
            await self.gpControlCommand("digital_zoom?range_pcnt=" + zoomLevel)

    async def getMedia(self):
        """Return url for media
        """
        if "FS" in (await self.infoCamera(constants.Camera.Firmware)):
            await self.getMediaFusion()
        else:
            folder = ""
            file_lo = ""
            try:
                json_parse = await self._client.getJSON('http://' + self.ip_addr + ':8080/gp/gpMediaList')
                for i in json_parse['media']:
                    folder = i['d']
                for i in json_parse['media']:
                    for i2 in i['fs']:
                        file_lo = i2['n']
                return "http://" + self.ip_addr + ":8080/videos/DCIM/" + folder + "/" + file_lo
            except (HTTPError, URLError) as error:
                return ""
                print("Error code:" + str(error.code) +
                      "\nMake sure the connection to the WiFi camera is still active.")
            except timeout:
                return ""
                print("HTTP Timeout\nMake sure the connection to the WiFi camera is still active.")

    def getMediaFusion(self):
        folder_1 = ""
        folder_2 = ""
        file_1 = ""
        file_2 = ""
        try:
            raw_data = urllib.request.urlopen('http://' + self.ip_addr + ':8080/gp/gpMediaListEx').read().decode('utf-8')
            json_parse = json.loads(raw_data)
            for i in json_parse[0]['media']:
                folder_1 = i['d']
                if "GBACK" in i['d']:
                    folder_2 = i['d'].replace("GBACK", "GFRNT")
                else:
                    folder_2 = i['d'].replace("GFRNT", "GBACK")
            for mediaitem in json_parse[0]['media']:
                if mediaitem["d"] == folder_1:
                    for mediaitem2 in mediaitem["fs"]:
                        file_1 = mediaitem2["n"]
            for mediaitem in json_parse[1]['media']:
                if mediaitem["d"] == folder_2:
                    for mediaitem2 in mediaitem["fs"]:
                        file_2 = mediaitem2["n"]

            return [
                "http://" + self.ip_addr + ":8080/videos/DCIM/" + folder_1 + "/" + file_1,
                "http://" + self.ip_addr + ":8080/videos2/DCIM/" + folder_2 + "/" + file_2]
        except (HTTPError, URLError) as error:
            return ""
            print("Error code:" + str(error.code) + "\nMake sure the connection to the WiFi camera is still active.")
        except timeout:
            return ""
            print("HTTP Timeout\nMake sure the connection to the WiFi camera is still active.")

    async def getMediaInfo(self, option=None):
        """Return MediaInfo about last record in MediaList
        """
        folder = ""
        file = ""
        size = "0"
        json_parse = await self._client.getJSON('http://' + self.ip_addr + ':8080/gp/gpMediaList')

        if "FS" in (await self.infoCamera(constants.Camera.Firmware)):
            json_parse = json_parse[0]
        for i in json_parse['media']:
            folder = i['d']
        for i in json_parse['media']:
            for i2 in i['fs']:
                file = i2['n']
                size = i2['s']
        if option == 'file':
            return file
        elif option == 'folder':
            return folder
        elif option == 'size':
            return size

        return MediaInfo(file, folder, int(size))

    async def listMedia(self, format=True, media_array=True):
        """Returns a list of media records
        If format is False you get the raw parsed JSON.
        If media_array is True you will get an array MediaInfo
        If media_array is False you will get a comma separated string of filenames
        """
        parsed_resp = await self._client.getJSON('http://' + self.ip_addr + ':8080/gp/gpMediaList')
        if not parsed_resp:
            return []

        if format is False:
            return parsed_resp

        if media_array is True:
            media = []
            if "FS" in await self.infoCamera(constants.Camera.Firmware):
                medialength = len(parsed_resp)
                for i in range(medialength):
                    for folder in parsed_resp[i]['media']:
                        for item in folder['fs']:
                            media.append(MediaInfo(folder['d'], item['n'], item['s']))
            else:
                for i in parsed_resp['media']:
                    for i2 in i['fs']:
                        media.append(MediaInfo(i['d'], i2['n'], i2['s']))
            return media
        else:
            medialength = len(parsed_resp)
            msg = ''
            for i in range(medialength):
                for folder in parsed_resp[i]['media']:
                    for item in folder['fs']:
                        if len(msg) > 0:
                            msg += ', '
                        msg += item['n']
            return msg

    #
    # Misc media utils
    #

    async def IsBusy(self):
        if (await self.is_apitype("gpcontrol")):
            return (await self.getStatus(constants.Status.Status, constants.Status.STATUS.IsBusy))

        raise UnsupportedCameraError()

    def getInfoFromURL(self, url):
        media = []
        media.append(url.replace('http://' + self.ip_addr + ':8080/videos/DCIM/', '').replace('/', '-').rsplit('-', 1)[0])
        media.append(url.replace('http://' + self.ip_addr + ':8080/videos/DCIM/', '').replace('/', '-').rsplit('-', 1)[1])
        return media

    #
    # Downloading media functions
    #

    def downloadMultiShot(self, path=""):
        raise NotImplementedError('downloadMultiShot not implemented as async')
        if path == "":
            path = self.getMedia()
            folder = self.getInfoFromURL(path)[0]
            filename = self.getInfoFromURL(path)[1]
            arr = json.loads(self.listMedia())
            lower_bound = 0
            high_bound = 0
            for i in arr['media']:
                for i2 in i['fs']:
                    if i['d'] == folder:
                        for i in arr['media']:
                            for i2 in i['fs']:
                                if i2['n'] == filename:
                                    lower_bound = i2["b"]
                                    high_bound = i2["l"]
            for i in range(int(high_bound) - int(lower_bound) + 1):
                f = filename[:4] + str(int(lower_bound) + i) + ".JPG"
                self.downloadMedia(folder, f)
        else:
            folder = self.getInfoFromURL(path)[0]
            filename = self.getInfoFromURL(path)[1]
            arr = json.loads(self.listMedia())
            lower_bound = 0
            high_bound = 0
            for i in arr['media']:
                for i2 in i['fs']:
                    if i['d'] == folder:
                        for i in arr['media']:
                            for i2 in i['fs']:
                                if i2['n'] == filename:
                                    lower_bound = i2["b"]
                                    high_bound = i2["l"]
            for i in range(int(high_bound) - int(lower_bound) + 1):
                f = filename[:4] + str(int(lower_bound) + i) + ".JPG"
                self.downloadMedia(folder, f)

    async def downloadLastMedia(self, path="", custom_filename=""):
        if (await self.IsBusy()) == 0:
            if path == "":
                media = await self.getMediaInfo()
                self._handle_log("downloadLastMedia - filename:{0} size: {1}".format(media.name, media.size), media=media)
                if custom_filename == "":
                    custom_filename = "{0}-{1}".format(media.folder, media.name)

                media = await self.getMedia()
                if "FS" in (await self.infoCamera(constants.Camera.Firmware)):
                    await asyncio.gather(
                        self._client.download(media[0].replace("JPG", "GPR"), "100GBACK-{0}".format(media.name)),
                        self._client.download(media[1].replace("JPG", "GPR"), "100GFRNT-{0}".format(media.name))
                    )
                else:
                    await self._client.download(media, custom_filename)
            else:
                self._handle_log("filename: " + self.getInfoFromURL(path)[1])
                filename = ""
                if custom_filename == "":
                    filename = self.getInfoFromURL(path)[0] + "-" + self.getInfoFromURL(path)[1]
                else:
                    filename = custom_filename
                await self._client.download(path, filename)
        else:
            print("Not supported while recording or processing media.")

    async def downloadMedia(self, media, custom_filename=""):
        if not isinstance(media, MediaInfo):
            raise Exception('Wrong parameter type for media')

        if (await self.IsBusy()) == 0:
            filename = ""
            if custom_filename == "":
                filename = media.name
            else:
                filename = custom_filename

            self._handle_log("downloadMedia - Downloading {3} bytes {0}/{1} to {2}".format(
                media.folder, media.name, filename, self.parse_value("media_size", media.size)))
            await self._client.download("http://" + self.ip_addr + ":8080/videos/DCIM/" + media.folder + "/" + media.name, filename)
        else:
            raise Exception("Not supported while recording or processing media.")

    async def downloadAll(self, option=""):
        """Downloads all media with folder-filename naming
        option "video" only downloads MP4 and "photos" only JPG
        Returns list of downloaded files
        """
        media_stash = []
        files = await self.listMedia()
        filtered_files = files

        if option == "videos":
            filtered_files = [fil for fil in files if fil.name.endswith("MP4")]
        elif option == "photos":
            filtered_files = [fil for fil in files if fil.name.endswith("JPG")]

        tasks = []
        for fil in filtered_files:
            tasks.append(self.downloadMedia(fil, "{0}-{1}".format(fil.folder, fil.name)))
            media_stash.append(fil)
        await asyncio.gather(*tasks)
        return media_stash

    def downloadLowRes(self, path="", custom_filename=""):
        if self.IsBusy() == 0:
            if path == "":
                url = self.getMedia()
                lowres_url = ""
                lowres_filename = ""
                if url.endswith("MP4"):
                    lowres_url = self.getMedia().replace('MP4', 'LRV')
                    if "GH" in lowres_url:
                        lowres_url = lowres_url.replace("GH", "GL")
                    lowres_filename = "LOWRES" + self.getMediaInfo("folder") + "-" + self.getMediaInfo("file")
                else:
                    print("not supported")
                print("filename: " + lowres_filename)
                print(lowres_url)
                if custom_filename == "":
                    try:
                        urllib.request.urlretrieve(lowres_url, lowres_filename)
                    except (HTTPError, URLError) as error:
                        print("ERROR: " + str(error))
                else:
                    try:
                        urllib.request.urlretrieve(lowres_url, custom_filename)
                    except (HTTPError, URLError) as error:
                        print("ERROR: " + str(error))
            else:
                lowres_url = ""
                lowres_filename = ""
                if path.endswith("MP4"):
                    lowres_url = path.replace('MP4', 'LRV')
                    if "GH" in lowres_url:
                        lowres_url = lowres_url.replace("GH", "GL")
                    lowres_filename = "LOWRES" + path.replace('MP4', 'LRV').replace('http://' + self.ip_addr + ':8080/videos/DCIM/', '').replace('/', '-')
                else:
                    print("not supported")
                print("filename: " + lowres_filename)
                print(lowres_url)
                if custom_filename == "":
                    try:
                        urllib.request.urlretrieve(lowres_url, lowres_filename)
                    except (HTTPError, URLError) as error:
                        print("ERROR: " + str(error))
                else:
                    try:
                        urllib.request.urlretrieve(lowres_url, custom_filename)
                    except (HTTPError, URLError) as error:
                        print("ERROR: " + str(error))
        else:
            print("Not supported while recording or processing media.")
    #
    # Query Media Info
    #

    async def getVideoInfo(self, option="", folder="", file=""):
        # TODO: always return full object. Then we don't have to ask that many times
        if option == "":
            if folder == "" and file == "":
                [fileInfo, folderInfo] = await asyncio.gather(self.getMediaInfo("file"),
                                                              self.getMediaInfo("folder"))

                if fileInfo.endswith("MP4"):
                    return await self._client.getText(
                        'http://' + self.ip_addr + ':8080/gp/gpMediaMetadata?p=' + folderInfo +
                        "/" + fileInfo + '&t=videoinfo')
        else:
            data = ""
            if folder == "" and file == "":
                [fileInfo, folderInfo] = await asyncio.gather(self.getMediaInfo("file"),
                                                              self.getMediaInfo("folder"))
                data = await self._client.getText(
                    'http://' + self.ip_addr + ':8080/gp/gpMediaMetadata?p=' + folderInfo + "/" +
                    fileInfo + '&t=videoinfo')
            if folder == "":
                if not file == "":
                    if file.endswith("MP4"):
                        folderInfo = await self.getMediaInfo("folder")
                        data = await self._client.getText(
                            'http://' + self.ip_addr + ':8080/gp/gpMediaMetadata?p=' + folderInfo +
                            "/" + file + '&t=videoinfo')
            if not file == "" and not folder == "":
                data = await self._client.getText(
                    'http://' + self.ip_addr + ':8080/gp/gpMediaMetadata?p=' + folder +
                    "/" + file + '&t=videoinfo')
            jsondata = json.loads(data)
            self._log_handler("getVideoInfo({0}, {1}, {2}) > {3}".format(option, folder, file, data), result=jsondata[option])
            return jsondata[option]  # dur/tag_count/tags/profile/w/h

    def getPhotoInfo(self, option="", folder="", file=""):
        if option == "":
            if folder == "" and file == "":
                if self.getMediaInfo("file").endswith("JPG"):
                    return urllib.request.urlopen(
                        'http://' + self.ip_addr + ':8080/gp/gpMediaMetadata?p=' + self.getMediaInfo("folder") +
                        "/" + self.getMediaInfo("file") + '&t = v4info').read().decode('utf-8')
        else:
            data = ""
            if folder == "" and file == "":
                if self.getMediaInfo("file").endswith("JPG"):
                    data = urllib.request.urlopen(
                        'http://' + self.ip_addr + ':8080/gp/gpMediaMetadata?p=' + self.getMediaInfo("folder") +
                        "/" + self.getMediaInfo("file") + '&t = v4info').read().decode('utf-8')
            if folder == "":
                if not file == "":
                    if file.endswith("JPG"):
                        data = urllib.request.urlopen(
                            'http://' + self.ip_addr + ':8080/gp/gpMediaMetadata?p=' + self.getMediaInfo("folder") +
                            "/" + file + '&t = v4info').read().decode('utf-8')
            if not file == "" and not folder == "" and file.endswith("JPG"):
                data = urllib.request.urlopen(
                    'http://' + self.ip_addr + ':8080/gp/gpMediaMetadata?p=' + folder + "/" +
                    file + '&t = v4info').read().decode('utf-8')
            jsondata = json.loads(data)
            return jsondata[option]  # "w":"4000","h":"3000" / "wdr":"0","raw":"0"

    def getPhotoEXIF(self, option="", folder="", file=""):
        if option == "":
            if folder == "" and file == "":
                if self.getMediaInfo("file").endswith("JPG"):
                    return urllib.request.urlopen(
                        'http://' + self.ip_addr + ':8080/gp/gpMediaMetadata?p=' + self.getMediaInfo("folder") + "/" +
                        self.getMediaInfo("file") + '&t = exif').read().decode('utf-8')
        else:
            data = ""
            if folder == "" and file == "":
                if self.getMediaInfo("file").endswith("JPG"):
                    data = urllib.request.urlopen(
                        'http://' + self.ip_addr + ':8080/gp/gpMediaMetadata?p=' + self.getMediaInfo("folder") + "/" +
                        self.getMediaInfo("file") + '&t = exif').read().decode('utf-8')
            if folder == "":
                if not file == "":
                    if file.endswith("JPG"):
                        data = urllib.request.urlopen(
                            'http://' + self.ip_addr + ':8080/gp/gpMediaMetadata?p=' +
                            self.getMediaInfo("folder") + "/" + file + '&t = exif').read().decode('utf-8')
            if not file == "" and not folder == "" and file.endswith("JPG"):
                data = urllib.request.urlopen(
                    'http://' + self.ip_addr + ':8080/gp/gpMediaMetadata?p=' + folder + "/" + file + '&t = exif').read().decode('utf-8')
            jsondata = json.loads(data)
            return jsondata[option]

    #
    # Clip functions
    #

    async def getClip(self, file, resolution, frame_rate, start_ms, stop_ms):
        out = ""
        if "HERO4" in (await self.infoCamera("model_name")):
            out = await self.gpControlCommand(
                "transcode/request?source=DCIM/" + file + "&res=" + resolution + "&fps_divisor=" +
                frame_rate + "&in_ms=" + start_ms + "&out_ms=" + stop_ms)
        else:
            out = await self.gpControlCommand(
                "transcode/video_to_video?source=DCIM/" + file + "&res=" + resolution + "&fps_divisor=" +
                frame_rate + "&in_ms=" + start_ms + "&out_ms=" + stop_ms)

        return out["status"]["id"]

    async def clipStatus(self, status):
        if not isinstance(status, str):
            status = str(status)
        resp = await self.gpControlCommand("transcode/status?id=" + status)
        resp_parsed = resp["status"]["status"]
        return constants.Clip.TranscodeStage[resp_parsed]

    async def getClipURL(self, status):
        if not isinstance(status, str):
            status = str(status)
        resp = await self.gpControlCommand("transcode/status?id=" + status)
        resp_parsed = resp["status"]["status"]
        if resp_parsed == 2:
            return "http://" + self.ip_addr + ":80/videos/" + resp["status"]["output"]

    def cancelClip(self, video_id):
        self.gpControlCommand("transcode/cancel?id=" + video_id)

    #
    # Livestreaming functions
    #

    def livestream(self, option):
        if option == "start":
            if self.whichCam() == "gpcontrol":
                print(self.gpControlExecute('p1=gpStream&a1=proto_v2&c1=restart'))
            else:
                print(self.sendCamera("PV", "02"))
        if option == "stop":
            if self.whichCam() == "gpcontrol":
                print(self.gpControlExecute('p1=gpStream&a1=proto_v2&c1=stop'))
            else:
                print(self.sendCamera("PV", "00"))

    def stream(self, addr, quality=""):
        self.livestream("start")
        if self.whichCam() == "gpcontrol":
            if "HERO4" in self.infoCamera("model_name"):
                if quality == "high":
                    self.streamSettings("2400000", "6")
                elif quality == "medium":
                    self.streamSettings("1000000", "4")
                elif quality == "low":
                    self.streamSettings("250000", "0")
            else:
                if quality == "high":
                    self.streamSettings("4000000", "7")
                elif quality == "medium":
                    self.streamSettings("1000000", "4")
                elif quality == "low":
                    self.streamSettings("250000", "0")
            subprocess.Popen("ffmpeg -f mpegts -i udp://" + self.ip_addr + ":8554 -b 800k -r 30 -f mpegts " + addr, shell=True)
            self.KeepAlive()
        elif self.whichCam() == "auth":
            subprocess.Popen("ffmpeg -i http://" + self.ip_addr + ":8080/live/amba.m3u8 -f mpegts " + addr, shell=True)

    def streamSettings(self, bitrate, resolution):
        self.gpControlSet("62", bitrate)
        self.gpControlSet("64", resolution)

    def parse_value(self, param, value):
        if param == "video_left":
            return str(time.strftime("%H:%M:%S", time.gmtime(value)))
        if param == "rem_space":
            if value == 0:
                return "No SD"
            ammnt = 1000
            if self.whichCam() == "gpcontrol" and self.infoCamera("model_name") == "HERO4 Session":
                ammnt = 1
            size_bytes = value * ammnt
            size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
            i = int(math.floor(math.log(size_bytes, 1024)))
            p = math.pow(1024, i)
            size = round(size_bytes / p, 2)
            storage = "" + str(size) + str(size_name[i])
            return str(storage)
        if param == "media_size":
            if isinstance(value, str):
                value = float(value)
            size_bytes = value
            size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
            i = int(math.floor(math.log(size_bytes, 1024)))
            p = math.pow(1024, i)
            size = round(size_bytes / p, 2)
            storage = "" + str(size) + str(size_name[i])
            return str(storage)
        if self.whichCam() == "gpcontrol":
            if param == "mode":
                if value == 0:
                    return "Video"
                if value == 1:
                    return "Photo"
                if value == 2:
                    return "Multi-Shot"
            if param == "sub_mode":
                if self.getStatus(constants.Status.Status, constants.Status.STATUS.Mode) == 0:
                    if value == 0:
                        return "Video"
                    if value == 1:
                        return "TimeLapse Video"
                    if value == 2:
                        return "Video+Photo"
                    if value == 3:
                        return "Looping"

                if self.getStatus(constants.Status.Status, constants.Status.STATUS.Mode) == 1:
                    if value == 0:
                        return "Single Pic"
                    if value == 1:
                        return "Burst"
                    if value == 2:
                        return "NightPhoto"

                if self.getStatus(constants.Status.Status, constants.Status.STATUS.Mode) == 2:
                    if value == 0:
                        return "Burst"
                    if value == 1:
                        return "TimeLapse"
                    if value == 2:
                        return "Night lapse"

            if param == "recording":
                if value == 0:
                    return "Not recording - standby"
                if value == 1:
                    return "RECORDING!"

            if param == "battery":
                if value == 0:
                    return "Nearly Empty"
                if value == 1:
                    return "LOW"
                if value == 2:
                    return "Halfway"
                if value == 3:
                    return "Full"
                if value == 4:
                    return "Charging"

            if param == "video_res":
                if value == 1:
                    return "4k"
                elif value == 2:
                    return "4kSV"
                elif value == 4:
                    return "2k"
                elif value == 5:
                    return "2kSV"
                elif value == 6:
                    return "2k4by3"
                elif value == 7:
                    return "1440p"
                elif value == 8:
                    return "1080pSV"
                elif value == 9:
                    return "1080p"
                elif value == 10:
                    return "960p"
                elif value == 11:
                    return "720pSV"
                elif value == 12:
                    return "720p"
                elif value == 13:
                    return "480p"
                elif value == 14:
                    return "5.2K"
                elif value == 15:
                    return "3K"
                else:
                    return "out of scope"
            if param == "video_fr":
                if value == 0:
                    return "240"
                elif value == 1:
                    return "120"
                elif value == 2:
                    return "100"
                elif value == 5:
                    return "60"
                elif value == 6:
                    return "50"
                elif value == 7:
                    return "48"
                elif value == 8:
                    return "30"
                elif value == 9:
                    return "25"
                elif value == 10:
                    return "24"
                else:
                    return "out of scope"
        else:
            raise UnsupportedCameraError()

    async def overview(self, mapped=False):
        if (await self.is_apitype("gpcontrol")):
            overview = await self.getStatus()
            if mapped:
                overview.status.SubMode = Parsers.sub_mode(overview.status.Mode, overview.status.SubMode)
                overview.status.Mode = Parsers.mode(overview.status.Mode)

                overview.status.RemVideoTime = Parsers.video_left(overview.status.RemVideoTime)
                overview.status.BatteryLevel = Parsers.battery(overview.status.BatteryLevel)
                overview.status.RemainingSpace = Parsers.rem_space(overview.status.RemainingSpace, self._camera.model)
                overview.status.IsBusy = Parsers.recording(overview.status.IsBusy)

                overview.settings.Resolution = Parsers.video_res(overview.settings.Resolution)
                overview.settings.Framerate = Parsers.video_fr(overview.settings.Framerate)
            return overview
        raise UnsupportedCameraError()

    async def connect(self, camera='detect'):
        self._handle_log('#connect - ' + camera)
        if camera == "detect":
            self._camera = await self.whichCam()
            self._handle_connect(self._camera)
        elif camera == "startpair":
            self.pair()
        else:
            if camera == "auth" or camera == "HERO3" or camera == "HERO3+" or camera == "HERO2":
                self.power_on_auth()
                time.sleep(2)
                self._camera = "auth"
            else:
                self._camera = "gpcontrol"
                self.power_on(self._mac_address)
                self.prepare_gpcontrol()
            print("Connected to " + self.ip_addr)

    async def quit(self):
        await self._client.quit()

    def on_connect(self):
        def decorator(handler):
            self._connect_handler = handler
            return handler
        return decorator

    def _handle_connect(self, camera):
        if self._connect_handler is not None:
            self._connect_handler(camera)

    def on_log(self):
        def decorator(handler):
            self._log_handler = handler
            return handler
        return decorator

    def _handle_log(self, message, **kwargs):
        if self._log_handler is not None:
            try:
                self._log_handler(message, **kwargs)
            except Exception:
                raise
