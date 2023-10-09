import json


class TagsManager:
    tags = []

    def __init__(self) -> None:
        with open("tags.json", "r") as file:
            config_data = json.load(file)

            for tag_type in config_data["types"]:
                tag_type_name = tag_type["name"]
                tags = [
                    "::".join([tag_type_name, tag["name"]]) for tag in tag_type["tags"]
                ]

                self.tags.extend(tags)

    def get_tags(self):
        return self.tags

    def get_index(self, tag_name: str) -> int:
        return self.tags.index(tag_name)

    def get_num_of_tags(self):
        return len(self.tags)
