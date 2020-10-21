try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    description='Data extraction and processing for genre prediction using ML',
    version='0.1.0',
    install_requires=['requests', 'pandas', 'numpy', 'tabulate', 'youtube_dl', 'ffmpeg', 'pydub', 'librosa'],
    packages=['model'],
    name='genreml',
    python_requires='>=3.5',
    entry_points={
        'console_scripts': [
                'genreml = model.__main__:main'
            ]
    }
)
