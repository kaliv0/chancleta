<p align="center">
  <img src="https://github.com/kaliv0/chancleta/blob/main/assets/chancleta.gif?raw=true" width="250" alt="Chancleta Samurai">
</p>

# chancleta

![Python 3.x](https://img.shields.io/badge/python-3.12-blue?style=flat-square&logo=Python&logoColor=white)
[![PyPI](https://img.shields.io/pypi/v/chancleta.svg)](https://pypi.org/project/chancleta/)

<br>Python library for creating <b>command line interfaces</b> in a composable way via configuration files.
<br> Supports <i>.toml</i>, <i>.json</i>, <i>.yaml</i>. and (if you'd like to be more adventurous) <i>.xml</i>.

---------------------------
### How to use
- Describe configurations in a chancleta.toml file. 
<br>(File format could vary between .toml, .json, .yaml and .xml as long as the name remains the same.)
<br>Add mandatory <i>'meta'</i> data with general information about your program

```toml
[meta]
src = "testoo.util.commands"
prog = "foo"
version = "0.1.0"
description = "Test my new flip flops"
usage = "Take that jive Jack, put it in your pocket 'til I get back"
```
<b>'src'</b> points to the directory where the corresponding python functions are to be found and called with arguments read from the terminal
- Configure subcommands as separate tables (objects if you're using JSON)

```toml
[yes]
description = "Simple yes function"
argument = { name = "text", help = "Some dummy text" }
option = { name = "should-repeat", short = "r", flag = "True", help = "should repeat text 5 times" }
help = "yes func"
function = "yes"
```
<b>function</b> shows the name of the python function to be called
- If you have multiple arguments/options - put them as inline tables inside arrays
```toml
[echo]
arguments = [
    { name = "text", help = "Some dummy text" },
    { name = "mark", type = "str", help = "Final mark" },
]
options = [
    { name = "other-text", short = "o", default = "Panda", dest = "other", help = "Some other dummy text" },
    { name = "delimiter", default = ", ", help = "use DELIM instead of TAB for field delimiter" },
    { name = "num", default = 42, type = "int", help = "some random number to make things pretty" }
]
function = "echo"
```
<i>chancleta</i> supports advanced features such as <i>choices</i>, <i>nargs</i>, <i>dest</i> (for options), <i>type</i> validation
```toml
[maybe]
argument = { name = "number", type = "int", choices = [3, 5, 8], help = "Some meaningless number" }
option = { name = "other-number", type = "int", nargs = "*", choices = [1, 2], dest = "other", help = "Other marvelous number" }
function = "maybe"
```
- For boolean flags you could use
 ```toml
options = [
    { name = "should-log", flag = "False", default = true },
    { name = "should-repeat", flag = "True"}
]
```
which is equivalent to
```
action="store_false"...
action="store_true"...
```
- If no <i>short</i> name is given for an option, the first letter of the full name is used
---------------------------

- Inside your program import the <i>Chancleta</i> object, pass a path to the directory where your config file lives and call the <i>parse</i> method
```python
from chancleta import Chancleta

def main():
    Chancleta("./testoo/config").parse()
```
If no path is given chancleta will try to find the config file inside the root directory of your project