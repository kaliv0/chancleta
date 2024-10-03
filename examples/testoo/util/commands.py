def echo(text, other, delimiter, num, mark):
    print(f"{text}{delimiter}{other}{num}{mark}")


def yes(text, should_repeat):
    times = 5 if should_repeat else 2
    for _ in range(times):
        print(text)


def no(text, other, should_log):
    if should_log:
        print("-".join(text))
    else:
        print("Chancleta samurai")

    if other:
        print(" ".join(other))


def maybe(number, other):
    print(f"{number} => {other}")
