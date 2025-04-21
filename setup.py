from pathlib import Path
from setuptools import setup, find_packages

BASE_DIR = Path(__file__).parent
long_description = (BASE_DIR / "README.md").read_text(encoding="utf-8")

def parse_requirements(filename):
    with open(BASE_DIR / filename) as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
setup(
    name="pyflow",
    version="0.1.0",
    
    # Структура пакета
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,

    # Зависимости
    install_requires=parse_requirements("requirements.txt"),
    python_requires=">=3.10",

    # Метаданные
    author="Лях Лилиана",
    description="CLI инструмент для работы с Python проектами",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lyakhliliana/pyflow",

    # Точки входа для CLI
    entry_points={
        "console_scripts": [
            "pyflow=interfaces.cli.cli:main",
        ],
    },
)
