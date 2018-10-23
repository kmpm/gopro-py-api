from setuptools import setup
with open("README.md", "r") as fh:
      long_description = fh.read()
setup(name='goprocam',
      version='2.0.10',
      description='GoPro WiFi API Wrapper for Python with asyncio',
      url='http://github.com/kmpm/py-asyncio-goproapi',
      long_description=long_description,
      long_description_content_type="text/markdown",
      author='Konrad Iturbe',
      author_email='mail@chernowii.com',
      license='MIT',
      packages=['goprocam'],
      install_requires=[
            'aiohttp>=3.4.4'
      ],
      test_suite='tests',
      zip_safe=False)
