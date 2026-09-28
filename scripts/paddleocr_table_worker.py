"""External worker: ordinary PaddleOCR only; never imported by the core parser."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--device", default="gpu:0")
    parser.add_argument("--language", default="en")
    args = parser.parse_args()

    import paddleocr
    from paddleocr import PaddleOCR

    engine = PaddleOCR(
        lang=args.language,
        device=args.device,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
    )
    results = list(engine.predict(input=args.input))
    if len(results) != 1:
        raise RuntimeError(f"Expected one OCR result, received {len(results)}")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    results[0].save_to_json(str(output))
    print(json.dumps({
        "output": output.name,
        "result_count": 1,
        "paddleocr_version": getattr(paddleocr, "__version__", None),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
