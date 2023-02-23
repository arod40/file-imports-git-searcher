from argparse import ArgumentParser

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--foo", action="store_true")

    args = parser.parse_args()
    print(args)