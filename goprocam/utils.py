import math
import functools
import inspect
import warnings
import json
import time

from goprocam import constants

string_types = (type(b''), type(u''))

__all__ = ['Struct', 'media_size', 'deprecated']

STATUS_MAP = {}
for key, value in vars(constants.Status.STATUS).items():
    STATUS_MAP[value] = key


class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)


class Parsers:
    @staticmethod
    def mode(value):
        if value == 0:
            return "Video"
        if value == 1:
            return "Photo"
        if value == 2:
            return "Multi-Shot"

    @staticmethod
    def sub_mode(modevalue, value):
        if modevalue == 0:
            if value == 0:
                return "Video"
            if value == 1:
                return "TimeLapse Video"
            if value == 2:
                return "Video+Photo"
            if value == 3:
                return "Looping"

        if modevalue == 1:
            if value == 0:
                return "Single Pic"
            if value == 1:
                return "Burst"
            if value == 2:
                return "NightPhoto"

        if modevalue == 2:
            if value == 0:
                return "Burst"
            if value == 1:
                return "TimeLapse"
            if value == 2:
                return "Night lapse"

    @staticmethod
    def recording(value):
        if value == 0:
            return "Standby"
        if value == 1:
            return "Recording"

    @staticmethod
    def battery(value):
        if value == 0:
            return "Empty"
        if value == 1:
            return "Low"
        if value == 2:
            return "Halfway"
        if value == 3:
            return "Full"
        if value == 4:
            return "Charging"

    @staticmethod
    def video_res(value):
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

    @staticmethod
    def video_fr(value):
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

    @staticmethod
    def video_left(value):
        return str(time.strftime("%H:%M:%S", time.gmtime(value)))

    @staticmethod
    def rem_space(value, model_name):
        if value == 0:
                return "No SD"
        ammnt = 1000
        if model_name == "HERO4 Session":
            ammnt = 1
        size_bytes = value * ammnt
        return media_size(size_bytes)


def remap_key(data, map):
    data_mapped = {}
    for key, value in data.items():
        try:
            data_mapped[map[key]] = value
        except KeyError:
            pass
    return data_mapped


def reconstruct_status(data):
    status = data['status']
    settings = data['settings']
    status_mapped = {}
    settings_mapped = {}
    if status:
        status_mapped = remap_key(status, STATUS_MAP)

    if settings:
        settings_mapped['Framerate'] = settings[constants.Video.FRAME_RATE]
        settings_mapped['Resolution'] = settings[constants.Video.RESOLUTION]

    return Struct(**{'status': Struct(**status_mapped), 'settings': Struct(**settings_mapped)})


def dump_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, sort_keys=True, indent=4, ensure_ascii=False)


def media_size(value):
    """Generates a human readable value from bytes
    """
    if isinstance(value, str):
        value = float(value)
    size_bytes = value
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    size = round(size_bytes / p, 2)
    storage = "" + str(size) + str(size_name[i])
    return str(storage)


def deprecated(reason):
    """
    This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used.
    """

    if isinstance(reason, string_types):

        # The @deprecated is used with a 'reason'.
        #
        # .. code-block:: python
        #
        #    @deprecated("please, use another function")
        #    def old_function(x, y):
        #      pass

        def decorator(func1):

            if inspect.isclass(func1):
                fmt1 = "Call to deprecated class {name} ({reason})."
            else:
                fmt1 = "Call to deprecated function {name} ({reason})."

            @functools.wraps(func1)
            def new_func1(*args, **kwargs):
                warnings.simplefilter('always', DeprecationWarning)
                warnings.warn(
                    fmt1.format(name=func1.__name__, reason=reason),
                    category=DeprecationWarning,
                    stacklevel=2
                )
                warnings.simplefilter('default', DeprecationWarning)
                return func1(*args, **kwargs)

            return new_func1

        return decorator

    elif inspect.isclass(reason) or inspect.isfunction(reason):

        # The @deprecated is used without any 'reason'.
        #
        # .. code-block:: python
        #
        #    @deprecated
        #    def old_function(x, y):
        #      pass

        func2 = reason

        if inspect.isclass(func2):
            fmt2 = "Call to deprecated class {name}."
        else:
            fmt2 = "Call to deprecated function {name}."

        @functools.wraps(func2)
        def new_func2(*args, **kwargs):
            warnings.simplefilter('always', DeprecationWarning)
            warnings.warn(
                fmt2.format(name=func2.__name__),
                category=DeprecationWarning,
                stacklevel=2
            )
            warnings.simplefilter('default', DeprecationWarning)
            return func2(*args, **kwargs)

        return new_func2

    else:
        raise TypeError(repr(type(reason)))
