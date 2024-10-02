def echo(text, other, delimiter, mark):
    print(f"{text}{delimiter}{other}{mark}")


def yes(text, should_repeat):
    times = 5 if should_repeat else 2
    for _ in range(times):
        print(text)
