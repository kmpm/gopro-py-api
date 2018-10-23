import asyncio
import aiohttp
import os
import posixpath
try:
    from urlparse import urlsplit
    from urllib import unquote
except ImportError: # Python 3
    from urllib.parse import urlsplit, unquote


class UrlHelper:
    def __init__(self, **kwargs):
        self.session = False
        self.download_semaphore = asyncio.Semaphore(kwargs.pop('download_semaphore', 4))
        self.chunk_size=kwargs.pop('chunk_size', 64*1024)
    
    async def setup(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def quit(self):
        await self.session.close()
        
    async def getText(self, url, timeout=30):
        async with self.session.get(url, timeout=timeout) as resp:
            return await resp.text()


    async def getJSON(self, url, timeout=30):
        async with self.session.get(url, timeout=timeout) as resp:
            return await resp.json()
    
    async def download(self, url, filename=None):
        async with self.download_semaphore:
            if not filename:
                filename = url2filename(url)
            
            async with self.session.get(url) as resp:
                with open(filename, 'wb') as fd:
                    while True:
                        chunk = await resp.content.read(self.chunk_size)
                        if not chunk:
                            break
                        fd.write(chunk)
                

    
        


        

        


def url2filename(url):
    """Return basename corresponding to url.
    >>> print(url2filename('http://example.com/path/to/file%C3%80?opt=1'))
    fileÀ
    >>> print(url2filename('http://example.com/slash%2fname')) # '/' in name
    Traceback (most recent call last):
    ...
    ValueError
    """
    urlpath = urlsplit(url).path
    basename = posixpath.basename(unquote(urlpath))
    if (os.path.basename(basename) != basename or
        unquote(posixpath.basename(urlpath)) != basename):
        raise ValueError  # reject '%2f' or 'dir%5Cbasename.ext' on Windows
    return basename
        