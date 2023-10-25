from typing import List
from AnnotationRoi import AnnotationRoi, AnnotationRoiEventObserver
import csv
from pyqtgraph import PlotWidget
from util import log_method_call


class AnnotationManager(AnnotationRoiEventObserver):
    def __init__(self) -> None:
        pass

    annotations: List[AnnotationRoi] = []

    @log_method_call
    def add(self, annotation: AnnotationRoi):
        overlapping_annotations: List[AnnotationRoi] = []

        # Find overlapping annotations
        for existing_annotation in self.annotations:
            if (
                annotation.annotation_type == existing_annotation.annotation_type
                and self.is_overlapping(existing_annotation, annotation)
            ):
                overlapping_annotations.append(existing_annotation)

        # Update overlapping annotations
        for overlapping_annotation in overlapping_annotations:
            overlap_area = self.calculate_overlap(overlapping_annotation, annotation)
            if overlap_area > 0:
                overlapping_annotation.delete_roi(None)

        self.annotations.append(annotation)
        annotation.add_observer(self)

    @log_method_call
    def save_to_csv(self, filename, x_min: int, x_max: int):
        with open(filename, "w", newline="", encoding="utf-8") as csv_file:
            csv_writer = csv.writer(csv_file)

            csv_writer.writerow(["start_timestamp", "end_timestamp", "behavior"])

            for annotation in self.annotations:
                if (annotation.x_start < x_min and annotation.x_end < x_min) or (
                    annotation.x_start > x_max and annotation.x_end > x_max
                ):
                    print(f"{annotation} has been ignored.")
                    continue

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

    def clear(self):
        for annotation in self.annotations:
            annotation.clear()
        self.annotations.clear()

    @log_method_call
    def load_from_csv(self, filename, plot_widget: PlotWidget):
        with open(filename, "r", encoding="utf-8") as csv_file:
            csv_reader = csv.reader(csv_file)

            next(csv_reader)

            for row in csv_reader:
                start_timestamp = int(row[0])
                end_timestamp = int(row[1])
                behavior = row[2]

                self.add(
                    AnnotationRoi(
                        plot_widget,
                        start_timestamp / 1000.0,
                        end_timestamp / 1000.0,
                        behavior,
                    )
                )

    def is_overlapping(self, annotation1: AnnotationRoi, annotation2: AnnotationRoi):
        # Implement the logic to check if two annotations are overlapping
        # For example, you can check if start_x of one annotation is less than end_x of the other annotation
        return (
            annotation1.x_start <= annotation2.x_end
            and annotation2.x_start <= annotation1.x_end
        )

    def calculate_overlap(self, annotation1: AnnotationRoi, annotation2: AnnotationRoi):
        # Calculate the area of overlap between two annotations
        overlap_area = min(annotation1.x_end, annotation2.x_end) - max(
            annotation1.x_start, annotation2.x_start
        )
        return max(0, overlap_area)

    def get_annotations(self, x: int) -> List[AnnotationRoi]:
        matching_annotations = []

        for annotation in self.annotations:
            if annotation.x_start <= x <= annotation.x_end:
                matching_annotations.append(annotation)

        return matching_annotations
