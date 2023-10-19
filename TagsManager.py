import json


class TagsManager:
    _instance = None  # Private class variable to store the single instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TagsManager, cls).__new__(cls)
            cls._instance.initialize()  # Initialize the instance
        return cls._instance

    def initialize(self):
        self.tags = []
        self.types = []

        with open("tags.json", "r") as file:
            config_data = json.load(file)

            for tag_type in config_data["types"]:
                tag_type_name = tag_type["name"]
                self.types.append(tag_type_name)

                self.tags.extend(
                    [
                        "::".join([tag_type_name, tag["name"], tag["description"]])
                        for tag in tag_type["tags"]
                    ]
                )

    def get_tags(self):
        return self.tags

    def get_index(self, tag_name: str) -> int:
        return self.tags.index(tag_name)

    def get_index_of_type(self, type_name: str) -> int:
        return self.types.index(type_name)

    def get_num_of_types(self):
        return len(self.types)

    def get_num_of_tags(self):
        return len(self.tags)
