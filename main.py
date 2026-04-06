import argparse
import sys
from uploader import run


def main():
    parser = argparse.ArgumentParser(description="Login and upload a document via Playwright.")
    parser.add_argument("file", help="Path to the file you want to upload")
    args = parser.parse_args()

    run(args.file)


if __name__ == "__main__":
    main()
