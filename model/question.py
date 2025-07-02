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
    def __init__(
        self,
        stem: str,
        answer: Union[int, str, None],
        choices: Optional[List[str]] = None,
        explanation: Optional[str] = None,
        conditions: Optional[str] = None,
        metadata: Optional[Metadata] = None,
        passage_id: str = None,
        question_number: int = None,
        image_path: str = None
    ):
        self.stem = stem
        self.choices = choices
        self.answer = answer
        self.explanation = explanation
        self.conditions = conditions
        self.metadata = metadata or Metadata(type="etc", difficulty="중", points=None)
        self.passage_id = passage_id
        self.question_number = question_number
        self.image_path = image_path

    def to_dict(self):
        return {
            "stem": self.stem,
            "choices": self.choices,
            "answer": self.answer,
            "explanation": self.explanation,
            "conditions": self.conditions,
            "metadata": self.metadata.to_dict(),
            "passage_id": self.passage_id,
            "question_number": self.question_number,
            "image_path": self.image_path
        }