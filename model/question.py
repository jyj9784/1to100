from typing import Optional, Union, List

class Metadata:
    def __init__(self, type: str, difficulty: str, points: Optional[str] = None):
        self.type = type
        self.difficulty = difficulty
        self.points = points

    def to_dict(self):
        return {
            "type": self.type,
            "difficulty": self.difficulty,
            "points": self.points
        }

class Question:
    def __init__(self, stem: str, metadata: Metadata, passage_id: str, question_number: int, choices: Optional[List[str]] = None, answer: Optional[str] = None, image_path: Optional[str] = None, choices_image_path: Optional[str] = None):
        self.stem = stem
        self.choices = choices
        self.answer = answer
        self.metadata = metadata
        self.passage_id = passage_id
        self.question_number = question_number
        self.image_path = image_path
        self.choices_image_path = choices_image_path

    def to_dict(self) -> dict:
        return {
            "stem": self.stem,
            "choices": self.choices,
            "answer": self.answer,
            "metadata": self.metadata.to_dict(),
            "passage_id": self.passage_id,
            "question_number": self.question_number,
            "image_path": self.image_path,
            "choices_image_path": self.choices_image_path
        }