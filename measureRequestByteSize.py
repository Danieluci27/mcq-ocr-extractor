import json
import sys

def batch_size_bytes(batch_requests: list[dict]) -> int:
    if not isinstance(batch_requests, (dict, list)):
        try:
            batch_requests = batch_requests.model_dump()
        except AttributeError:
            raise TypeError("batch_requests must be dict/list or convertible")

    json_str = json.dumps(batch_requests, ensure_ascii=False)
    return len(json_str.encode("utf-8"))