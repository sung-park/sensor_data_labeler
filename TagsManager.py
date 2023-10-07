import json


class TagsManager:
    def __init__(self) -> None:
        with open("tags.json", "r") as file:
            config_data = json.load(file)
            self.tags = [tag["name"] for tag in config_data.get("tags", [])]

    def get_tags(self):
        return self.tags

    def get_index(self, tag_name: str) -> int:
        return self.tags.index(tag_name)

    def get_num_of_tags(self):
        return len(self.tags)
