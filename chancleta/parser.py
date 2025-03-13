import os


class Chancleta:
    CONFIG_FILE = "chancleta"
    CONFIG_FORMATS = [".toml", ".json", ".yaml", ".xml"]

    EMPTY_CONFIG_ERROR = "Empty configuration file {config_path}"
    MISSING_CONFIG_ERROR = "Missing configuration file in {cwd}"
    NON_SUPPORTED_TABLE_ERROR = "Top level tables are not supported"
    MISSING_TABLE_ERROR = "Missing mandatory 'meta' table"
    MISSING_TABLE_KEY_ERROR = "Missing key '{key}' in table '{table}'"
    MISSING_PARAM_KEY_ERROR = "Missing key '{key}' for '{parameter}' parameter in table '{table}'"

    def __init__(self, cwd=os.getcwd()):
        self.cwd = cwd
        self.data = None
        self.parser = None
        self.subparsers = None
        self.func_src = None
        self.func_args = None

    # ### config ###
    def _handle_config(self):
        for config_fmt in self.CONFIG_FORMATS:
            config_path = os.path.join(self.cwd, f"{self.CONFIG_FILE}{config_fmt}")
            if not os.path.exists(config_path):
                continue
            if not os.path.getsize(config_path):
                raise ValueError(self.EMPTY_CONFIG_ERROR.format(config_path=config_path))
            return self._read_file(config_path)
        raise ValueError(self.MISSING_CONFIG_ERROR.format(cwd=self.cwd))

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
        return bool(self.data)

    # ### CLI ###
    def _read_args(self):
        import argparse
        import importlib

        self.parser = argparse.ArgumentParser()
        self.subparsers = self.parser.add_subparsers(help="sub-commands")

        if "meta" not in self.data:
            raise KeyError(self.MISSING_TABLE_ERROR)

        for table_name, table_data in self.data.items():
            if not isinstance(table_data, dict):
                raise SyntaxError(self.NON_SUPPORTED_TABLE_ERROR)

            if table_name == "meta":
                self._read_meta_table(table_name, table_data)
                continue
            # NB: if we don't pass 'help' as kwarg here and add it later as attribute it gets ignored
            subparser = self.subparsers.add_parser(
                table_name, help=table_data.get("help", None), prog=self.parser.prog
            )
            for entry_name, entry_data in table_data.items():
                match entry_name:
                    case "argument" | "arguments":
                        self._handle_subparser_args(table_name, entry_name, entry_data, subparser)
                    case "option" | "options":
                        self._handle_subparser_args(
                            table_name, entry_name, entry_data, subparser, is_option=True
                        )
                    case "description":
                        subparser.description = entry_data

            if not (func_name := table_data.get("function", None)):
                raise KeyError(self.MISSING_TABLE_KEY_ERROR.format(key="function", table=table_name))
            subparser.set_defaults(func=getattr(importlib.import_module(self.func_src), func_name))  # noqa
        self.func_args = self.parser.parse_args()

    # ### read 'meta' ###
    def _read_meta_table(self, table_name, table_data):
        self.func_src = table_data.get("src", None)
        if not self.func_src:
            raise KeyError(self.MISSING_TABLE_KEY_ERROR.format(key="src", table=table_name))
        for entry_name, entry_data in table_data.items():
            match entry_name:
                case "prog":
                    self.parser.prog = entry_data
                case "description":
                    self.parser.description = entry_data
                case "usage":
                    self.parser.usage = entry_data
                case "version":
                    self.parser.add_argument("--version", action="version", version=entry_data)

    # ### handle sub-commands ###
    def _handle_subparser_args(self, table_name, entry_name, entry_data, subparser, is_option=False):
        if isinstance(entry_data, list):
            for argument in entry_data:
                self._add_subparser_arg(table_name, entry_name, argument, subparser, is_option)
        else:
            self._add_subparser_arg(table_name, entry_name, entry_data, subparser, is_option)

    def _add_subparser_arg(self, table_name, entry_name, entry_data, subparser, is_option):
        import builtins

        if not (name := entry_data.get("name", None)):
            raise KeyError(
                self.MISSING_PARAM_KEY_ERROR.format(key="name", parameter=entry_name, table=table_name)
            )
        kwargs = {
            "help": entry_data.get("help", None),
        }
        if not is_option:
            args = (name,)
            kwargs["action"] = "store"
        else:
            args = (f"--{name}", f"-{entry_data['short'] if entry_data.get('short', None) else name[0]}")
            kwargs.update(
                {
                    "default": entry_data.get("default", None),
                    "dest": entry_data.get("dest", None),
                    "action": self._flag_action(entry_data),
                }
            )
        # for arguments and options -> if not booleans
        if kwargs["action"] == "store":
            kwargs.update(
                {
                    "type": (
                        getattr(builtins, arg_type) if (arg_type := entry_data.get("type", None)) else None
                    ),
                    "nargs": entry_data.get("nargs", None),
                    "choices": entry_data.get("choices", None),
                }
            )
        subparser.add_argument(*args, **kwargs)

    @staticmethod
    def _flag_action(entry_data):
        match entry_data.get("flag", None):
            case "True":
                return "store_true"
            case "False":
                return "store_false"
        return "store"

    # ### run ###
    def _run_func(self):
        import inspect

        func = self.func_args.func
        params = {param: getattr(self.func_args, param) for param in inspect.signature(func).parameters}
        func(**params)

    def parse(self):
        self._handle_config()
        self._read_args()
        self._run_func()
