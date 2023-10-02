from typing import List
from AnnotationRoi import AnnotationRoi
import csv


class AnnotationManager:
    def __init__(self) -> None:
        pass

    annotations: List[AnnotationRoi] = []

    def add(self, annotation):
        self.annotations.append(annotation)

    def save_to_csv(self, filename):
        with open(filename, "w", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)

            csv_writer.writerow(["start_timestamp", "end_timestamp", "behavior"])

            for annotation in self.annotations:
                csv_writer.writerow(
                    [
                        int(annotation.x_start * 1000),
                        int(annotation.x_end * 1000),
                        annotation.annotation_text,
                    ]
                )
