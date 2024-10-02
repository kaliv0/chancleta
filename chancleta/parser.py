import os


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
    MISSING_TABLE_KEY_ERROR = "Missing key '{key}' in table '{table}'"
    MISSING_PARAM_KEY_ERROR = "Missing key '{key}' for '{parameter}' parameter in table '{table}'"

    def __init__(self, cwd="./"):
        self.cwd = cwd
        self.data = None
        self.config_type = None
        self.parser = None
        self.subparsers = None
        self.func_src = None
        self.func_args = None

    # ### config ###
    def validate_read_config(self):
        for config in self.CONFIG_FILES:
            config_path = os.path.join(self.cwd, config)
            if not os.path.exists(config_path):
                continue
            if not os.path.getsize(config_path):
                return False
            return self._read_file(config_path)
        return False

    def _read_file(self, config_path):
        with open(config_path, "rb") as f:
            _, extension = os.path.splitext(config_path)
            match extension:
                case ".toml":
                    import tomllib

                    self.data = tomllib.load(f)
                case ".json":
                    import json

                    self.data = json.load(f)
                case ".yaml":
                    import yaml

                    self.data = yaml.safe_load(f)
                case _:
                    import xmltodict

                    self.data = xmltodict.parse(f)["root"]
        self.config_type = extension[1:]
        return bool(self.data)

    # ### CLI ###
    def read_args(self):
        import argparse
        import importlib

        self.parser = argparse.ArgumentParser()
        self.subparsers = self.parser.add_subparsers(help="sub-commands")

        if "meta" not in self.data:
            raise KeyError(self.MISSING_TABLE_ERROR)

        for k, v in self.data.items():
            if not isinstance(v, dict):
                raise TypeError("Top level tables are not supported")

            if k == "meta":
                self._read_meta_table(k, v)
                continue
            # NB: if we don't pass 'help' as kwarg here and add it later as attribute it gets ignored for some reason?!
            subparser = self.subparsers.add_parser(
                k, help=v.get("help", None), prog=self.parser.prog
            )  # TODO: check if manually setting 'prog' is necessary
            for sk, sv in v.items():
                match sk:
                    case "argument" | "arguments":
                        self._handle_subparser_args(k, sk, subparser, sv)
                    case "option" | "options":
                        self._handle_subparser_args(k, sk, subparser, sv, is_option=True)
                    case "description":
                        subparser.description = sv

            if not (func_name := v.get("function", None)):
                raise KeyError(self.MISSING_TABLE_KEY_ERROR.format(key="function", table=k))
            subparser.set_defaults(func=getattr(importlib.import_module(self.func_src), func_name))  # noqa
        self.func_args = self.parser.parse_args()

    # ### read 'meta' ###
    def _read_meta_table(self, k, v):
        self.func_src = v.get("src", None)
        if not self.func_src:
            raise KeyError(self.MISSING_TABLE_KEY_ERROR.format(key="src", table=k))
        for sk, sv in v.items():
            match sk:
                case "prog":
                    self.parser.prog = sv
                case "description":
                    self.parser.description = sv
                case "usage":
                    self.parser.usage = sv
                case "version":
                    self.parser.add_argument("--version", action="version", version=sv)

    # ### handle sub-commands ###
    def _handle_subparser_args(self, k, sk, subparser, sv, is_option=False):
        if isinstance(sv, list):
            for arg in sv:
                self._add_subparser_arg(k, sk, arg, subparser, is_option)
        else:
            self._add_subparser_arg(k, sk, sv, subparser, is_option)

    def _add_subparser_arg(self, k, sk, sv, subparser, is_option):
        import builtins

        if not (name := sv.get("name", None)):
            raise KeyError(self.MISSING_PARAM_KEY_ERROR.format(key="name", parameter=sk, table=k))
        kwargs = {
            "help": sv.get("help", None),
        }
        if not is_option:
            args = (name,)
        else:
            args = (f"--{name}", f"-{sv['short'] if sv.get('short', None) else name[0]}")

            kwargs.update(
                {
                    "default": sv.get("default", None),
                    "dest": sv.get("dest", None),  # works only for options
                    "action": self._flag_action(sv),
                }
            )
        # for arguments and options -> if not booleans
        if not kwargs.get("action", None):
            kwargs["type"] = getattr(builtins, arg_type) if (arg_type := sv.get("type", None)) else None
            kwargs["nargs"] = sv.get("nargs", None)
        subparser.add_argument(*args, **kwargs)

    @staticmethod
    def _flag_action(sv):
        match sv.get("flag", None):
            case "True":
                return "store_true"
            case "False":
                return "store_false"
        return None

    # ### run ###
    def run_func(self):
        import inspect

        func = self.func_args.func
        params = {p: getattr(self.func_args, p) for p in inspect.signature(func).parameters}
        func(**params)

    def parse(self):
        if not self.validate_read_config():
            return
        self.read_args()
        self.run_func()
