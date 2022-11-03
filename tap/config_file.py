import json

import shlex
from typing import Optional, Callable, List

from tap.utils import as_python_object
import logging


class ConfigFile:
    """
    Arg type that instructs tap to load arguments from the file specified.
    This represents a "runtime" config file in the sense that the filename
    is specified by the user on the cli (e.g. --conf testing.json),
    as opposed to by the developer in source code (via the config_files
    parameter to the Tap constructor).
    """
    def __init__(self, config_path: str):
        self.config_path = config_path

    def _extract_args_json(self):
        """extract cli args from json file"""
        args = []
        with open(self.config_path) as f:
            config_dict = json.load(f, object_hook=as_python_object)
            for key, value in config_dict.items():
                valtype = type(value)
                args += [f'--{key}']
                if valtype == str or valtype == int or valtype == float or valtype == bool:
                    args += [f"{value}"]
                elif valtype == list:
                    args += [f"{x}" for x in value]
        return args

    def _extract_args_txt(self):
        """extract cli args from text file"""
        with open(self.config_path) as f:
            return shlex.split(f.read().strip())

    def _get_extractor(self) -> Optional[Callable]:
        """get the function responsible for extracting args"""
        extension = self.config_path.lower().split(".")[-1]
        if extension == "json":
            return self._extract_args_json
        elif extension == "txt" or extension == "text":
            return self._extract_args_txt
        return None

    def extract_args(self) -> List[str]:
        """extract cli args in the config file"""
        extractor = self._get_extractor()
        if not extractor:
            logging.warning(f"unable to infer file type from {self.config_path}, trying text ...")
            extractor = self._extract_args_txt
        return extractor()


