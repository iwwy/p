import os

from setuptools import setup, find_packages


here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.rst")) as f:
    README = f.read()
with open(os.path.join(here, "CHANGES.rst")) as f:
    CHANGES = f.read()

requires = [
    ]

setup(name="Project",
      version="0.1",
      description="Proof of concept WSGI framework.",
      long_description=README + "\n\n" + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        ],
      author="Roman Danilov",
      author_email="danil_rom@yahoo.com",
      url="https://github.com/iwwy/p",
      keywords="wsgi python demo",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      # entry_points={ "console_scripts": ["server = poc.wsgi:server"]}
  )
