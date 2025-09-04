import ast
import json
import argparse
from typing import Tuple


class GraphProcessor:
    def __init__(self) -> None:
        self.edges = []

    def load_from_csv(self, file_path: str) -> None:
        print('-' * 80)
        with open(file_path, "r") as file:
            file_content = file.read()

        rows = file_content.split("\n")
        for row in rows:
            try:
                evaluated_row = ast.literal_eval(f"[{row}]")
                self.add_edge(evaluated_row)
            except Exception as error:
                print(f"Error processing row '{row}': {error}")
        print('\n'.join(str(edge) for edge in self.edges))
        print('-' * 80)

    def add_edge(self, edge: Tuple[int]) -> None:
        self.edges.append(edge)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('csv_path')
    args = parser.parse_args()

    processor = GraphProcessor()
    processor.load_from_csv(args.csv_path)

    return


if __name__ == "__main__":
    main()
