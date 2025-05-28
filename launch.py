import io
import os
import json
import base64
import requests
from bson import ObjectId
from typing import List, Dict, Union
from PyPDF2 import PdfReader, PdfWriter
from schema import PredictSchema


def merge_pagewise_jsons_unique_values_only(
    page_jsons: List[Dict[str, str]],
) -> Dict[str, Union[str, List[Dict[str, Union[str, int]]]]]:
    if not page_jsons:
        return {}
    final_result = {}
    keys = page_jsons[0].keys()

    for key in keys:
        seen = {}
        for idx, page in enumerate(page_jsons):
            value = page.get(key, "N/A")
            if value != "N/A":
                seen.setdefault(value, []).append(idx)
        if not seen:
            final_result[key] = "N/A"
        elif len(seen) == 1:
            unique_value = next(iter(seen))
            final_result[key] = unique_value
        else:
            # Multiple unique values found

            final_result[key] = [
                {"value": val, "page_number": idxs[0] + 1} for val, idxs in seen.items()
            ]
    return final_result


def split_pdf_base64_to_pagewise(base64_pdf: str):
    pdf_bytes = base64.b64decode(base64_pdf)
    pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
    page_base64_list = []

    for i, page in enumerate(pdf_reader.pages):
        pdf_writer = PdfWriter()
        pdf_writer.add_page(page)

        page_stream = io.BytesIO()
        pdf_writer.write(page_stream)
        page_stream.seek(0)
        page_base64 = base64.b64encode(page_stream.read()).decode("utf-8")
        page_base64_list.append({"page_number": i + 1, "base64": page_base64})
    return page_base64_list

def preprocessing():
    return None

def loadmodel():
    return None


def predict(payload: PredictSchema):
    base64_splits = split_pdf_base64_to_pagewise(payload["data"])
    file_extension = payload["file_path"].split(".")[-1]
    print(f"Total pages: {str(len(base64_splits))}")
    EXTRACTION_PREDICT_ENDPOINT = os.environ["EXTRACTION_PREDICT_ENDPOINT"]
    EXTRACTION_SECURE_TOKEN = os.environ["EXTRACTION_SECURE_TOKEN"]

    HANDWRITTEN_PREDICT_ENDPOINT = os.environ["HANDWRITTEN_PREDICT_ENDPOINT"]
    HANDWRITTEN_SECURE_TOKEN = os.environ["HANDWRITTEN_SECURE_TOKEN"]

    page_wise_results = []
    individual_page_readability = []
    for idx in range(len(base64_splits)):
        print(f"Page No. {idx+1}")
        data = {
            "data": base64_splits[idx]["base64"],
            "file_path": f"{str(ObjectId())}.{file_extension}",
        }
        extract_result = requests.post(
            EXTRACTION_PREDICT_ENDPOINT,
            json=data,
            headers={"Authorization": EXTRACTION_SECURE_TOKEN},
        )
        page_wise_results.append(json.loads(extract_result.text))

        readability_result = requests.post(
            HANDWRITTEN_PREDICT_ENDPOINT,
            json=data,
            headers={"Authorization": HANDWRITTEN_SECURE_TOKEN},
        )
        json_result = json.loads(readability_result.text)
        json_result["1"]["page_number"] = idx + 1
        individual_page_readability.append(json_result["1"])
    final_extracted_results = merge_pagewise_jsons_unique_values_only(
        page_wise_results
    )
    return {
        "extracted_values": final_extracted_results,
        "page_readability": individual_page_readability,
    }
