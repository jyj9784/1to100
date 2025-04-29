class Passage:
    def __init__(self, content: str):
        self.content = content

    def to_dict(self):
        return {"content": self.content}
