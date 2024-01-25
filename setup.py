from setuptools import setup

setup(
    name='dials-extensions',
    packages=["dials_extensions"],
    version='0.0.1',
    description='DIALS extensions for CHESS beamline ID7B2',
    author='Steve P. Meisburger',
    author_email='spm82@cornell.edu',
    url='https://github.com/FlexXBeamline/dials-extensions',
    license='BSD',
    python_requires=">=3.10",
    install_requires=[
        "dxtbx",
    ],
    entry_points={
        "dxtbx.format": [
            "FormatNXmxEigerFilewriterCHESS:FormatNXmxEigerFilewriter = dials_extensions.FormatNXmxEigerFilewriterCHESS:FormatNXmxEigerFilewriterCHESS"
        ],
    },
    include_package_data=True,
)
