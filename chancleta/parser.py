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
    MISSING_KEY_IN_TABLE_ERROR = "Missing key '{key}' in table '{table}'"
    MISSING_PARAM_NAME_ERROR = "Missing mandatory 'name' for parameter '{parameter}'"
    NOT_LIST_ERROR = "'{key}' is not a list"

    def __init__(self, cwd="./"):
        self.cwd = cwd
        self.data = None
        self.config_type = None

    def read_config(self):
        for config in self.CONFIG_FILES:
            # validate file
            config_path = os.path.join(self.cwd, config)
            if not os.path.exists(config_path):
                continue
            if not os.path.getsize(config_path):
                return False

            # read file
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

            # read 'meta' table
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
                    raise KeyError(self.MISSING_KEY_IN_TABLE_ERROR.format(key="src", table="meta"))
                continue

            # configure sub-commands
            subparser = subparsers.add_parser(k, help=v.get("help", None))
            for sk, sv in v.items():
                if sk in ("argument", "arguments"):
                    if not isinstance(sv, list):
                        # for xml only
                        if self.config_type != "xml":
                            raise TypeError(self.NOT_LIST_ERROR.format(key="arguments", table=k))
                        if not (name := sv.get("name", None)):
                            raise KeyError(self.MISSING_PARAM_NAME_ERROR.format(parameter=sk))
                        subparser.add_argument(
                            name,
                            help=sv.get("help", None),
                            action="store_true" if sv.get("is_flag", None) == "True" else None,
                        )
                    else:
                        for arg in sv:
                            if not (name := arg.get("name", None)):
                                raise KeyError(self.MISSING_PARAM_NAME_ERROR.format(parameter=sk))
                            subparser.add_argument(
                                name,
                                help=arg.get("help", None),
                                action="store_true" if arg.get("is_flag", None) == "True" else None,
                            )
                elif sk in ("option", "options"):
                    if not isinstance(sv, list):
                        # for xml only
                        if self.config_type != "xml":
                            raise TypeError(self.NOT_LIST_ERROR.format(key="options", table=k))
                        if not (name := sv.get("name", None)):
                            raise KeyError(self.MISSING_PARAM_NAME_ERROR.format(parameter=sk))
                        subparser.add_argument(
                            f"--{name}",
                            f"-{sv['short'] if sv.get('short', None) else name[0]}",
                            default=sv.get("default", None),
                            action="store_true" if sv.get("is_flag", None) == "True" else None,
                            dest=sv.get("dest", None),  # TODO: dest works only for options
                            help=sv.get("help", None),
                        )
                    else:
                        for opt in sv:
                            if not (name := opt.get("name", None)):
                                raise KeyError(self.MISSING_PARAM_NAME_ERROR.format(parameter=sk))
                            subparser.add_argument(
                                f"--{name}",
                                f"-{opt['short'] if opt.get('short', None) else name[0]}",
                                default=opt.get("default", None),
                                action="store_true" if opt.get("is_flag", None) == "True" else None,
                                dest=opt.get("dest", None),
                                help=opt.get("help", None),
                            )
                # TODO: implement
                elif sk == "description":
                    subparser.description = sv

            func_name = v.get("function", None)
            if func_name is None:
                raise KeyError(self.MISSING_KEY_IN_TABLE_ERROR.format(key="function", table=k))
            func = getattr(import_module(func_src), func_name)  # noqa
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
