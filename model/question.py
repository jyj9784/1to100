from typing import Optional, Union

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
        choices_text: Optional[str] = None,
        explanation: Optional[str] = None,
        conditions: Optional[str] = None,
        metadata: Optional[Metadata] = None
    ):
        self.stem = stem
        self.choices_text = choices_text
        self.answer = answer
        self.explanation = explanation
        self.conditions = conditions
        self.metadata = metadata or Metadata(type="etc", difficulty="중", points=None)

    def to_dict(self):
        return {
            "stem": self.stem,
            "choices_text": self.choices_text,
            "answer": self.answer,
            "explanation": self.explanation,
            "conditions": self.conditions,
            "metadata": self.metadata.to_dict()
        }