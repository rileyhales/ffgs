import os
import sys
from setuptools import setup, find_packages
from tethys_apps.app_installation import custom_develop_command, custom_install_command

# -- Apps Definition -- #
app_package = 'ffgs'
release_package = 'tethysapp-' + app_package
app_class = 'ffgs.app:Ffgs'
app_package_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tethysapp', app_package)

# -- Python Dependencies -- #
dependencies = ['']

setup(
    name=release_package,
    version='development',
    tags='FFGS, GFS, Flash Floods, Timeseries',
    description='An interface for viewing areas at risk for flood based on the FFGS',
    long_description='',
    keywords='FFGS',
    author='Riley Hales, Chris Edwards',
    author_email='',
    url='',
    license='BSD 3-Clause',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['tethysapp', 'tethysapp.' + app_package],
    include_package_data=True,
    zip_safe=False,
    install_requires=dependencies,
    cmdclass={
        'install': custom_install_command(app_package, app_package_dir, dependencies),
        'develop': custom_develop_command(app_package, app_package_dir, dependencies)
    }
)
