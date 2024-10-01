import argparse
import inspect
import os
import tomllib
import json
import yaml
import xmltodict
from importlib import import_module


class Chancleta:
    # fmt: off
    CONFIG_FILES = [
        "chancleta.toml",
        "chancleta.json",
        "chancleta.yaml",
        "chancleta.xml"
    ]
    # fmt: on

    MISSING_TABLE_ERROR = "Missing mandatory 'meta' table"
    MISSING_KEY_ERROR = "Missing key '{key}' in table '{table}'"
    NOT_LIST_ERROR = "'{key}' is not a list"

    def __init__(self, cwd="./"):
        self.cwd = cwd
        self.data = None
        self.config_type = None

    def read_config(self):
        for config in self.CONFIG_FILES:
            config_path = os.path.join(self.cwd, config)
            if not os.path.exists(config_path):
                continue
            if not os.path.getsize(config_path):
                return False

            with open(config_path, "rb") as f:
                _, extension = os.path.splitext(config_path)
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
        subparsers = parser.add_subparsers(help="sub-commands")

        if "meta" not in self.data:
            raise KeyError(self.MISSING_TABLE_ERROR)

        for k, v in self.data.items():
            if not isinstance(v, dict):
                raise TypeError("Top level tables are not supported")  # TODO: check terminology

            if k == "meta":
                func_src = None
                for sk, sv in v.items():
                    match sk:
                        case "src":
                            func_src = sv
                        case "prog":
                            parser.prog = sv
                        case "version":
                            parser.version = sv
                        case "description":
                            parser.description = sv

                if func_src is None:
                    raise KeyError(self.MISSING_KEY_ERROR.format(key="src", table="meta"))
                continue

            func_name = v.get("function", None)
            if func_name is None:
                raise KeyError(self.MISSING_KEY_ERROR.format(key="function", table=k))
            func = getattr(import_module(func_src), func_name)  # noqa

            # TODO: "help" etc should be optional
            subparser = subparsers.add_parser(k, help=v["help"])
            for sk, sv in v.items():
                # TODO: simplify -> if sk in ("argument", "arguments")
                if sk == "arguments" or (self.config_type == "xml" and sk == "argument"):
                    if not isinstance(sv, list):
                        if self.config_type != "xml":
                            raise TypeError(self.NOT_LIST_ERROR.format(key="arguments", table=k))
                        subparser.add_argument(sv["name"], help=sv["help"])
                    else:
                        for arg in sv:
                            subparser.add_argument(arg["name"], help=arg["help"])
                elif sk == "options" or (self.config_type == "xml" and sk == "option"):
                    if not isinstance(sv, list):
                        if self.config_type != "xml":
                            raise TypeError(self.NOT_LIST_ERROR.format(key="options", table=k))
                        # TODO: split and incrementally concatenate strings
                        subparser.add_argument(
                            f"--{sv['name']}",
                            f"-{sv['short']}",
                            default=sv["default"],
                            help=sv["help"],
                        )
                    else:
                        for opt in sv:
                            subparser.add_argument(
                                f"--{opt['name']}",
                                f"-{opt['short']}",
                                default=opt["default"],
                                help=opt["help"],
                            )

            subparser.set_defaults(func=func)
        return parser.parse_args()

    @staticmethod
    def run_func(args):
        func = args.func
        params = {p: getattr(args, p) for p in inspect.signature(func).parameters}
        func(**params)

    def parse(self):
        is_toml_file_valid = self.read_config()
        if not is_toml_file_valid:
            return
        args = self.read_args()
        self.run_func(args)
