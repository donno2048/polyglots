from setuptools import setup,find_packages
setup(
    name='polyglots',
    version='1.0.0',
    description='Create polyglots for different file types',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url='https://github.com/donno2048/polyglots',
    packages=find_packages(),
    license='MIT',
    author='Elisha Hollander',
    classifiers=['Programming Language :: Python :: 3'],
)