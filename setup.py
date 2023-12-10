from setuptools import setup

APP = ['Plante.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'packages': ['cv2', 'PIL', 'numpy', 'matplotlib'],
    'iconfile': 'icon.icns',  # Path to your .icns file
    'excludes': ['zmq'],
}


setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
