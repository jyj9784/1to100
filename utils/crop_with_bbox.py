import json
from pathlib import Path
from PIL import Image


def crop_images(json_path: str, output_dir: str) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for entry in data:
        img_path = Path(entry['path'])
        if not img_path.is_file():
            continue

        x1, y1, x2, y2 = entry['bbox']
        with Image.open(img_path) as img:
            cropped = img.crop((x1, y1, x2, y2))
            out_file = output_path / img_path.name
            cropped.save(out_file)
            print(f"[INFO] 저장 완료: {out_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="BBOX 영역으로 이미지 자르기")
    parser.add_argument('--json', default='data/question_images/ocr_results.json', help='bbox 정보가 담긴 JSON 경로')
    parser.add_argument('--out', default='data/cropped', help='잘라낸 이미지를 저장할 폴더')
    args = parser.parse_args()

    crop_images(args.json, args.out)
