from setuptools import setup, find_packages
setup(
    name='evez-osint',
    version='1.0.0',
    author='Steven Crawford-Maggard (EVEZ)',
    author_email='fiersteity@gmail.com',
    description='Suspect Inference Networking Matrix Engine -- eigenforensic OSINT analysis',
    url='https://github.com/EvezArt/evez-osint-engine',
    packages=find_packages(),
    python_requires='>=3.8',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Legal/Law Enforcement',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Programming Language :: Python :: 3',
    ],
    entry_points={'console_scripts': ['evez-osint=core.osint_cli:main']},
)
