from typing import List
from AnnotationRoi import AnnotationRoi, AnnotationRoiEventObserver
import csv

from util import log_method_call


class AnnotationManager(AnnotationRoiEventObserver):
    def __init__(self) -> None:
        pass

    annotations: List[AnnotationRoi] = []

    @log_method_call
    def add(self, annotation: AnnotationRoi):
        self.annotations.append(annotation)
        annotation.add_observer(self)

    @log_method_call
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

    @log_method_call
    def delete(self, annotation: AnnotationRoi):
        self.annotations.remove(annotation)
