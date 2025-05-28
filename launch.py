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


def predict(payload: PredictSchema):
    base64_splits = split_pdf_base64_to_pagewise(payload["data"])
    file_extension = payload["file_path"].split(".")[-1]
    print(f"Total pages: {str(len(base64_splits))}")
    EXTRACTION_PREDICT_ENDPOINT = "https://haier.katonic.ai/6703a1699e0b804e4879cc48/genai/gd-9679de75-084b-476b-9314-767e72049fba/api/v1/response"
    EXTRACTION_SECURE_TOKEN = "gd-9679de75-084b-476b-9314-767e72049fba-6703a1699e0b804e4879cc48-new eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3NjdlNzIwNDlmYmEtOGVlZDA3ZWVmNDZmNDI4MmI4MWI1MDkwYjY0OTQ0N2ZrYXRvbmljIiwiZXhwIjozMzI3MzgyNjgwODE3N30.HJ8y0PwMiqh_6f71VG5dQXkdoW4l8ipseLb2K9F0oTU"

    HANDWRITTEN_PREDICT_ENDPOINT = "https://haier.katonic.ai/6703a1699e0b804e4879cc48/genai/gd-0d66bc0f-03da-48b4-b031-8ee2c22eeeff/api/v1/response"
    HANDWRITTEN_SECURE_TOKEN = "gd-0d66bc0f-03da-48b4-b031-8ee2c22eeeff-6703a1699e0b804e4879cc48-new eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4ZWUyYzIyZWVlZmYtOGVlZDA3ZWVmNDZmNDI4MmI4MWI1MDkwYjY0OTQ0N2ZrYXRvbmljIiwiZXhwIjozMzI3Mzg4NzI5OTE3OX0.DI12UJytxQM7jvkZp478Q7FpKMcYQz6AZAVC3C5-EuA"

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
