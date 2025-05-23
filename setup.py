# coding: utf-8

from setuptools import setup

with open("readme.md", "r") as fh:
    long_description = fh.read()

setup(
    name="yambot_client",
    version="0.2.0",
    author="Anton Bugrin",
    author_email="abugrin@yandex.ru",
    description="Unofficial Client for Yandex Messenger Bot API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/abugrin/yambot",
    packages=['yambot'],
    classifiers=[
        'Development Status :: 4 - Beta',
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='python yandex.messenger api-client bot messaging',
    python_requires='>=3.8',
    install_requires=[
        'requests>=2.32.0',
        'urllib3>=2.0.0',
        'pydantic>=2.0.0'
    ],
    extras_require={
        'async': ['aiohttp>=3.9.0'],
        'httpx': ['httpx>=0.26.0'],
        'all': [
            'aiohttp>=3.9.0',
            'httpx>=0.26.0'
        ],
        'docs': [
            'sphinx>=7.1.2',
            'sphinx-rtd-theme>=1.3.0',
            'myst-parser>=2.0.0',
            'sphinxcontrib-napoleon>=0.7'
        ]
    }
)
