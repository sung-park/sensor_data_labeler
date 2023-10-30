import json
import os
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
    def save_to_ann(
        self,
        filename,
        x_min: int,
        x_max: int,
        offset: int,
        note_plain_text: str,
    ):
        ann_data = []
        for annotation in self.annotations:
            if (annotation.x_start < x_min and annotation.x_end < x_min) or (
                annotation.x_start > x_max and annotation.x_end > x_max
            ):
                print(f"{annotation} has been ignored.")
                continue

            json_entry = {
                "start_timestamp": int(annotation.x_start * 1000),
                "end_timestamp": int(annotation.x_end * 1000),
                "behavior": annotation.annotation_text,
            }
            ann_data.append(json_entry)

        json_data = {
            "annotations": ann_data,
            "meta": {
                "offset": offset,
                "note": note_plain_text,
            },
        }
        with open(filename, "w", encoding="utf-8") as jsonf:
            json.dump(json_data, jsonf, indent=4)

    @log_method_call
    def delete(self, annotation: AnnotationRoi):
        self.annotations.remove(annotation)

    def clear(self):
        for annotation in self.annotations:
            annotation.clear()
        self.annotations.clear()

    def convert_csv_to_json_if_needed(self, csv_filename: str):
        data = []

        with open(csv_filename, "r", encoding="utf-8") as file:
            try:
                csvreader = csv.reader(file)
                header = next(csvreader)  # Skip the header row
                if len(header) != 3:
                    print(f"The file '{csv_filename}' is not a valid CSV file.")
                    return

                for row in csvreader:
                    start_timestamp = int(row[0])
                    end_timestamp = int(row[1])
                    behavior = row[2]

                    json_entry = {
                        "start_timestamp": start_timestamp,
                        "end_timestamp": end_timestamp,
                        "behavior": behavior,
                    }

                    data.append(json_entry)
            except Exception as e:
                print(f"The file '{csv_filename}' is not a valid CSV file.")
                return

        print(f"The file '{csv_filename}' should be converted to JSON format!")

        org_filename = csv_filename + ".org"
        try:
            os.remove(org_filename)
        except FileNotFoundError:
            print(f"'{org_filename}' does not exist. No action taken.")
        os.rename(csv_filename, org_filename)

        if data:
            ann_data = []

            for row in data:
                start_timestamp = int(row["start_timestamp"])
                end_timestamp = int(row["end_timestamp"])
                behavior = row["behavior"]

                json_entry = {
                    "start_timestamp": start_timestamp,
                    "end_timestamp": end_timestamp,
                    "behavior": behavior,
                }

                ann_data.append(json_entry)

            json_data = {"annotations": data}
            with open(csv_filename, "w", encoding="utf-8") as jsonf:
                json.dump(json_data, jsonf, indent=4)
            print(f"Converted '{csv_filename}' to '{csv_filename}' successfully.")

    @log_method_call
    def load_from_ann(self, filename, plot_widget: PlotWidget) -> (int, str):
        self.convert_csv_to_json_if_needed(filename)

        with open(filename, "r", encoding="utf-8") as ann_file:
            data = json.load(ann_file)

            for entry in data.get("annotations", []):
                start_timestamp = entry.get("start_timestamp", 0)
                end_timestamp = entry.get("end_timestamp", 0)
                behavior = entry.get("behavior", "")

                self.add(
                    AnnotationRoi(
                        plot_widget,
                        start_timestamp / 1000.0,
                        end_timestamp / 1000.0,
                        behavior,
                    )
                )

            return (
                data.get("meta", {}).get("offset", None),
                data.get("meta", {}).get("note", None),
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

    def calculate_statistics(self, filename):
        behavior_durations = {}
        with open(filename, "r", encoding="utf-8") as filename:
            try:
                data = json.load(filename)
                for entry in data.get("annotations", []):
                    start_timestamp = entry.get("start_timestamp", 0)
                    end_timestamp = entry.get("end_timestamp", 0)
                    behavior = entry.get("behavior", "")

                    start_timestamp = int(start_timestamp)
                    end_timestamp = int(end_timestamp)
                    duration = end_timestamp - start_timestamp

                    if behavior in behavior_durations:
                        behavior_durations[behavior] += duration
                    else:
                        behavior_durations[behavior] = duration
            except Exception as e:
                pass
        return behavior_durations
