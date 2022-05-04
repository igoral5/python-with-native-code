'''
Created on 07.12.2021
Установка и сборка модуля mining
@author: ilalimov
'''
from setuptools import setup, Extension

module = Extension(
    'mining',
    sources=['mining.c'],
    libraries=['crypto', 'm'],
    extra_compile_args=['-Wall', '-Werror', '-O2']
)

setup(
    name='mining',
    version='0.0.1',
    ext_modules=[module]
)
