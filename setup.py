from setuptools import find_packages, setup

tests_requirements = [
    'pytest',
    'pytest-cov',
    'pytest-flake8',
    'pytest-isort',
]

setup(
    name="www-teepy",
    version="0.1.dev0",
    description="Website for BackOffice",
    url="https://www.lagestiondutierspayant.fr",
    author="Kozea",
    packages=find_packages(),
    include_package_data=True,
    scripts=['teepy.py'],
    install_requires=[
        'Flask',
        'mandrill',
        'libsass',
    ],
    tests_requires=tests_requirements,
    extras_require={'test': tests_requirements}
)
