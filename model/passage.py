from typing import Optional, List

class Passage:
    def __init__(self, content: str, passage_id: str = None, question_range: str = None, instruction: str = None, image_paths: List[str] = None):
        self.content = content
        self.passage_id = passage_id or "passage_1"
        self.question_range = question_range
        self.instruction = instruction
        self.image_paths = image_paths if image_paths is not None else []

    def to_dict(self):
        return {
            "id": self.passage_id,
            "content": self.content,
            "question_range": self.question_range,
            "instruction": self.instruction,
            "image_paths": self.image_paths
        }
