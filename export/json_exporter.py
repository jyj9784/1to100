import json
import os
from model.question import Question
from model.passage import Passage
from typing import List


def export_to_ilobag_json(
    set_title: str,
    passage: Passage,
    questions: List[Question],
    output_path: str
):
    data = {
        "set_title": set_title,
        "passages": [passage.to_dict()],
        "questions": [q.to_dict() for q in questions]
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[INFO] JSON 파일이 저장되었습니다: {output_path}")
