from __future__ import annotations

import argparse
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openai import OpenAI

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = BASE_DIR
ZERO_SHOT_DIR = os.path.join(PROJECT_DIR, "zero_shot")
DEFAULT_INPUT_DIR = os.path.join(PROJECT_DIR, "dataset", "valid", "input")

DEFAULT_SYSTEM_PROMPT = """\
あなたは日本古典籍OCRの誤り訂正システムです。

OCRによる明らかな誤字・脱字・衍字だけを、原文の文脈に基づいて訂正してください。
歴史的仮名遣い、旧字体、異体字、漢文調の表現は現代語に変更しないでください。
根拠のない補完、要約、説明、注釈を加えず、原文の内容と順序を維持してください。
修正後の本文のみを出力してください。
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run GPT zero-shot OCR correction on txt files.")
    parser.add_argument("--model", choices=("gpt-5.4", "gpt-5.5", "gpt-5.6-sol", "gpt-5.6-terra"), default="gpt-5.5")
    parser.add_argument("--input-dir", default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir")
    parser.add_argument("--max-new-tokens", type=int, default=1024)
    return parser.parse_args()


def resolve_output_dir(args: argparse.Namespace) -> str:
    if args.output_dir:
        return os.path.abspath(args.output_dir)

    return os.path.join(ZERO_SHOT_DIR, args.model, "output_base_valid")


def correct_with_openai(
    client: "OpenAI",
    ocr_text: str,
    model: str,
    max_new_tokens: int,
) -> tuple[str, float]:
    start_time = time.perf_counter()

    response = client.responses.create(
        model=model,
        instructions=DEFAULT_SYSTEM_PROMPT,
        input=ocr_text,
        max_output_tokens=max_new_tokens,
        temperature=0,
        top_p=1,
        reasoning={"effort": "none"},
        tools=[],
        tool_choice="none",
        text={"format": {"type": "text"}},
        store=False,
    )

    inference_time = time.perf_counter() - start_time
    return response.output_text.strip(), inference_time


def main() -> None:
    args = parse_args()
    output_dir = resolve_output_dir(args)

    if not os.path.isdir(args.input_dir):
        raise FileNotFoundError(f"Input directory not found: {args.input_dir}")

    from openai import OpenAI

    client = OpenAI()
    os.makedirs(output_dir, exist_ok=True)

    txt_files = sorted(Path(args.input_dir).glob("*.txt"))

    print(f"Model: {args.model}")
    print(f"Max new tokens: {args.max_new_tokens}")
    print(f"Input directory: {args.input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Found {len(txt_files)} files.")

    inference_times = []

    for idx, txt_path in enumerate(txt_files, start=1):
        output_path = Path(output_dir) / txt_path.name
        ocr_text = txt_path.read_text(encoding="utf-8").strip()

        corrected_text, inference_time = correct_with_openai(
            client=client,
            ocr_text=ocr_text,
            model=args.model,
            max_new_tokens=args.max_new_tokens,
        )
        inference_times.append(inference_time)

        output_path.write_text(corrected_text, encoding="utf-8")

        print(
            f"[{idx}/{len(txt_files)}] "
            f"Saved: {output_path} ({inference_time:.3f} s)"
        )

    if inference_times:
        print(
            "Average inference time: "
            f"{sum(inference_times) / len(inference_times):.3f} s/file"
        )


if __name__ == "__main__":
    main()
