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
    description = 'CLI tool that scans the working dir for text files, and looks for TODO and FIXME comments.',
    py_modules=['codetodo'],
    entry_points= {
        'console_scripts': [
            'codetodo = codetodo:main' 
        ]
    }
)
