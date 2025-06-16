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
        choices: Optional[List[str]] = None,  # choices만 유지
        explanation: Optional[str] = None,
        conditions: Optional[str] = None,
        metadata: Optional[Metadata] = None,
        number: Optional[str] = None,
    ):
        self.stem = stem
        self.choices = choices
        self.answer = answer
        self.explanation = explanation
        self.conditions = conditions
        self.metadata = metadata or Metadata(
            type="etc", difficulty="중", points=None)
        self.number = number

    def to_dict(self):
        return {
            "number": self.number,
            "stem": self.stem,
            "choices": self.choices,  # choices만 반환
            "answer": self.answer,
            "explanation": self.explanation,
            "conditions": self.conditions,
            "metadata": self.metadata.to_dict()
        }
