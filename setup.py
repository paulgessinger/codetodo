from setuptools import setup

# @TODO: Fix it! DONE
setup(
    name="codetodo",
    version="1.1",
    install_requires=[
        "tabulate",
        "termcolor",
        "rglob"
    ],
    author = 'Paul Gessinger',
    author_email = 'hello@paulgessinger.com',
    url = 'https://github.com/paulgessinger/codetodo',
    py_modules=['codetodo'],
    entry_points= {
        'console_scripts': [
            'codetodo = codetodo:main' 
        ]
    }
)
