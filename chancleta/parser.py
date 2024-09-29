import argparse
import inspect
import os
import tomllib
import json
import yaml
import xmltodict
from importlib import import_module


class Chancleta:
    CONFIG_FILES = ["chancleta.toml", "chancleta.json", "chancleta.yaml", "chancleta.xml"]

    MISSING_ERROR = "Missing key '{key}' in table '{table}'"
    NOT_LIST_ERROR = "'{key}' is not a list"

    def __init__(self):
        self.data = None
        self.config_type = None

    def read_config(self):
        for config in self.CONFIG_FILES:
            if not os.path.exists(config):
                continue
            if not os.path.getsize(config):
                return False

            with open(config, "rb") as f:
                _, extension = os.path.splitext(config)
                match extension:
                    case ".toml":
                        self.data = tomllib.load(f)
                    case ".json":
                        self.data = json.load(f)
                    case ".yaml":
                        self.data = yaml.safe_load(f)
                    case _:
                        self.data = xmltodict.parse(f)["root"]
            self.config_type = extension[1:]
            return bool(self.data)
        return False

    def read_args(self):
        parser = argparse.ArgumentParser()

        func_src = None
        func_name = None
        for k, v in self.data.items():
            if not isinstance(v, dict):
                raise TypeError("Top level tables are not supported")  # TODO: check terminology

            if k == "meta":
                for sk, sv in v.items():
                    if sk == "src":
                        func_src = sv
                    # TODO: read 'version' in same loop
                continue

            func_name = self.data[k].get("function", None)  # TODO: fix -> should be inside loop
            if func_name is None:
                raise KeyError(self.MISSING_ERROR.format(key="function", table=k))

            for sk, sv in v.items():
                # TODO: in xml these should singular
                if sk == "arguments" or (self.config_type == "xml" and sk == "argument"):
                    if not isinstance(sv, list):
                        if self.config_type != "xml":
                            raise TypeError(self.NOT_LIST_ERROR.format(key="arguments", table=k))
                        parser.add_argument(sv["name"])
                    else:
                        for arg in sv:
                            parser.add_argument(arg["name"])
                elif sk == "options" or (self.config_type == "xml" and sk == "option"):
                    if not isinstance(sv, list):
                        if self.config_type != "xml":
                            raise TypeError(self.NOT_LIST_ERROR.format(key="options", table=k))
                        parser.add_argument(f"--{sv['name']}", f"-{sv['short']}", help=sv["help"])
                    else:
                        # print(func_src)
                        func = getattr(import_module(func_src), func_name)
                        for opt in sv:
                            # TODO: split and incrementally concatenate string
                            parser.add_argument(
                                f"--{opt['name']}", f"-{opt['short']}", help=opt["help"]
                            )

        if func_src is None:
            raise KeyError(self.MISSING_ERROR.format(key="src", table="meta"))

        args = vars(parser.parse_args())
        # pprint(vars(args))
        params = {p: args[p] for p in inspect.signature(func).parameters}
        # pprint(params)
        func(**params)

    def parse(self):
        is_toml_file_valid = self.read_config()
        if not is_toml_file_valid:
            return
        # pprint(self.data)
        self.read_args()


if __name__ == "__main__":
    Chancleta().parse()
