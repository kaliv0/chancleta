def echo(text, other, delimiter):
    print(f"{text}{delimiter}{other}")


def yes(text, should_repeat):
    times = 5 if should_repeat else 2
    for _ in range(times):
        print(text)
