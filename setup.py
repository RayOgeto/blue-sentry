from setuptools import setup, find_packages

setup(
    name="bluesentry",
    version="1.0.0",
    description="Advanced BLE Scanner, Analyzer & Tracker",
    author="BlueSentry Team",
    py_modules=["scanner", "tracker", "vendors", "interrogator"],
    install_requires=[
        "bleak",
        "rich",
        "plotext"
    ],
    entry_points={
        'console_scripts': [
            'bluesentry=scanner:main_entry',
        ],
    },
)
