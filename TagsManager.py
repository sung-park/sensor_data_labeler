import json


class TagsManager:
    def __init__(self) -> None:
        with open("tags.json", "r") as file:
            config_data = json.load(file)
            self.tags = [tag["name"] for tag in config_data.get("tags", [])]

    def get_tags(self):
        return self.tags
