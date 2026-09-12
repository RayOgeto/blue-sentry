from setuptools import setup

setup(
    name="bluesentry",
    version="1.0.0",
    description="Advanced BLE Scanner, Analyzer & Tracker",
    author="BlueSentry Team",
    py_modules=["scanner", "tracker", "vendors", "interrogator"],
    python_requires=">=3.8",
    install_requires=[
        "bleak>=2.0.0",
        "rich>=13.0.0",
        "plotext>=5.2.0",
    ],
    entry_points={
        "console_scripts": [
            "bluesentry=scanner:main_entry",
        ],
    },
)
