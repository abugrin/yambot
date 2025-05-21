# coding: utf-8

from setuptools import setup

with open("readme.md", "r") as fh:
    long_description = fh.read()

setup(
    name="yambot_client",
    version="0.0.7",
    author="Anton Bugrin",
    author_email="abugrin@yandex.ru",
    description="Unofficial Client for Yandex Messenger Bot API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/abugrin/yambot",
    packages=['yambot'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='python yandex.messenger api-client',
    python_requires='>=3.8',
    install_requires=[
        'requests>=2.32.0'
    ]
)
