import os
from typing import List


class DynamoDBReservedWords:
    """
    Reserved Words used by DynamoDB that can cause issues,
    so they will need to be transformed under certain conditions, such as when doing projections
    """

    def __init__(self) -> None:
        self.__list: List[str] = self.__read_list()

    def words(self) -> List[str]:
        """Gets a list of dynamodb reserved words"""
        return self.__list

    def __read_list(self) -> List[str]:
        path = os.path.dirname(__file__)
        path = os.path.join(path, "dynamodb_reserved_words.txt")
        with open(path, "r", encoding="utf-8") as f:
            words = f.read().splitlines()
            # make sure they are all in uppercase
            for i, word in enumerate(words):
                words[i] = word.upper()
            return words

    def is_reserved_word(self, word: str) -> bool:
        """Checks if a word is a dynamodb reserved word"""
        return word.upper() in self.__list

    def tranform_projections(self, projections: List[str] | str) -> List[str]:
        """Transforms a list of projections to remove reserved words"""
        if isinstance(projections, str):
            projections = projections.split(",")

        # any projection that exists add a # infront of it
        projections = ["#" + p if self.is_reserved_word(p) else p for p in projections]
        return projections

    def transform_attributes(self, projections: List[str] | str) -> dict | None:
        """Transforms a dict of attributes to remove reserved words"""
        transformed_attributes: dict = {}
        if isinstance(projections, str):
            projections = projections.split(",")
        for item in projections:
            if self.is_reserved_word(item):
                transformed_attributes["#" + item] = item

        if len(transformed_attributes) > 0:
            return transformed_attributes
        return None
