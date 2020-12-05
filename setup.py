import pathlib

from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

setup(
    description='Data extraction and processing for genre prediction using ML',
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/adaros92/CS467-Project",
    version='0.3.4',
    install_requires=[
        'requests', 'pandas', 'numpy', 'tabulate', 'pydub', 'librosa', 'matplotlib', 'youtube_dl',
        'tensorflow', 'scikit-learn==0.22.2.post1'],
    tests_require=['pytest', 'pytest-cov'],
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=find_packages(exclude=("test",)),
    name='genreml',
    python_requires='>=3.5',
    package_data={
        'genreml': ['fma_data/*.mp3', 'model_resources/*', 'model/cnn/data/*']
    },
    entry_points={
        'console_scripts': [
            'genreml = genreml.model.__main__:main'
        ]
    }
)
