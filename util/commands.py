def echo(text, other_text, delimiter):
    delim = f" {delimiter * 2} " if delimiter else ", "
    print(f"{text}{delim}{other_text}")
