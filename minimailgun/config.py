"""
Read the config file and provide a global singleton.
"""

from os.path import dirname, join
import yaml


with open(join(dirname(__file__), 'config.yaml')) as config_file:
    config = yaml.load(config_file)
