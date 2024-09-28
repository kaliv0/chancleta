import argparse
import os
import tomllib
from importlib import import_module
from pprint import pprint
import inspect


class Chancleta:
    CONFIG_FILE = "chancleta.toml"

    def __init__(self):
        self.data = None

    def read_toml(self):
        if not (os.path.exists(self.CONFIG_FILE) and os.path.getsize(self.CONFIG_FILE)):
            return False

        with open(self.CONFIG_FILE, "rb") as f:
            self.data = tomllib.load(f)
        return bool(self.data)

    def read_args(self):
        parser = argparse.ArgumentParser()
        for k, v in self.data.items():
            if k == "src":
                continue

            # print(k)
            for sk, sv in v.items():
                # print(sk, sv)
                if sk == 'argument':
                    parser.add_argument(sv['name'])
                elif sk == 'option':
                    parser.add_argument(f"--{sv['name']}", f"-{sv['short']}", help=sv['help'])

        args = vars(parser.parse_args())
        # pprint(args)
        func = self.data['echo']['function']

        getattr(import_module(self.data['src']), func)(args)

    def parse(self):
        is_toml_file_valid = self.read_toml()
        if not is_toml_file_valid:
            return
        pprint(self.data)
        self.read_args()


if __name__ == '__main__':
    Chancleta().parse()
