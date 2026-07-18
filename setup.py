from setuptools import find_packages, setup


setup(
    name="techdoc-summary",
    version="0.1.0",
    description="CLI summaries for official technical documentation and release notes.",
    package_dir={"": "src"},
    packages=find_packages("src"),
    python_requires=">=3.9",
    extras_require={
        "dev": ["pytest>=8.0"],
    },
    entry_points={
        "console_scripts": [
            "techdoc-summary=techdoc_summary.cli:main",
        ],
    },
)
