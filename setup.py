import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dragino",
    version="0.0.2",
    author="Philip Basford",
    author_email="P.J.Basford@soton.ac.uk",
    description="A wrapper for the dragino LoRa/GPS HAT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url = "https://github.com/computenodes/dragino",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)'
    ],
    keywords="LoRaWAN",
    platforms='any',
    python_requires='>=3.3, <4',
    install_requires=['pyserial', 'configobj', 'spidev', 'rpi-gpio', 'pycrypto', 'pynmea2'],
    packages=setuptools.find_packages(),
)
