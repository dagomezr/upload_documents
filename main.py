import argparse
from uploader import run


def main():
    parser = argparse.ArgumentParser(description="Login and upload documents via Playwright.")
    parser.add_argument(
        "--batch-size",
        type=int,
        required=True,
        metavar="N",
        help="Max number of files to process per run",
    )
    args = parser.parse_args()
    run(batch_size=args.batch_size)


if __name__ == "__main__":
    main()
