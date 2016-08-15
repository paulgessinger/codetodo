from setuptools import setup

# @TODO: Fix it! DONE
setup(
    name="todopy",
    version="1.0",
    install_requires=[
        "tabulate",
        "termcolor",
        "rglob"
    ],
    author = 'Paul Gessinger',
    author_email = 'hello@paulgessinger.com',
    # scripts=['todo.py']
    py_modules=['todo'],
    entry_points= {
        'console_scripts': [
            'todopy = todo:main' 
        ]
    }
)
