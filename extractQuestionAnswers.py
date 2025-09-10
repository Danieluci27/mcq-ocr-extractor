from anthropic import Anthropic, RateLimitError
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request
from prompts import claude_ocr_system_prompt
from anthropic.types.messages.message_batch import MessageBatch
import os
import time
import base64

class ImageEncodingError(Exception):
    '''Exception raised for errors in the image encoding process.'''
    pass

class APIRequestError(Exception):
    '''Exception raised for errors during API requests.'''
    pass

class TimeoutError(Exception):
    '''Exception raised when a process exceeds the allocated time.'''
    pass

def encode_image_to_base64(path: str) -> str:
    '''
    Encode an input image to base64.

    path: local path to the image
    return: Base 64 encoding of an image
    '''
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Image file not found at path: {path}")
    
    if not path.lower().endswith(('.png', '.jpg', '.jpeg')):
        raise ImageEncodingError("Unsupported file format. Please use PNG or JPG images.")
    
    try:
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        raise ImageEncodingError(f"Error encoding image to base64: {e}")

def get_params(image_b64: str) -> MessageCreateParamsNonStreaming:
    return MessageCreateParamsNonStreaming(model= "claude-sonnet-4-20250514",
            max_tokens=1000,
            system=claude_ocr_system_prompt,
            temperature=0.1,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_b64
                            }
                             
                        },
                        {
                            "type": "text",
                            "text": "이미지에서 문제를 추출해 주세요."
                        }
                    ]
                }
            ]
    )

def create_request(paths: list[str]) -> list[Request]:
    '''
    Creates a list of request for batch inference

    paths: list of local URL of jpg files
    return: list of requests
    '''
    custom_id = 0
    requests = []
    for path in paths:
        try:
            image_b64 = encode_image_to_base64(path)
        except Exception as e:
            #Log the path that caused the error and continue with the next path
            print(f"ImageEncodingError for {path}: {e}")
            continue
        request = Request(
            custom_id=str(custom_id),
            params=get_params(image_b64)
        )
        requests.append(request)
        custom_id += 1
    return requests

def extract_problem_from_screenshot_on_batch(requests: list[Request], client: Anthropic) -> MessageBatch:
    '''
    Extract problems <question, answer options, correct answer> from a batch of screenshot images using Claude Sonnet OCR functionality.

    requests: the list of inference requests
    client: inference service provider; allows scheduling a batch inference.
    return MessageBatch object which includes the status of inference and batch id.
    '''
    try:
        batch_response = client.messages.batches.create(
            requests=requests
        )
        print(type(batch_response))
        return batch_response
    except RateLimitError:
        raise
    except Exception:
        raise

def extract_problem_from_screenshot_one_by_one(image_b64: str, client: Anthropic) -> str:
    '''
    Extract problem <question, answer, correct answer> from a screenshot image

    image_b64: base64 string representation of a screenshot image
    client: service provider; allows making a request for response generation
    return text extracted from response object
    '''
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=claude_ocr_system_prompt,
            temperature=0.1,
            messages=[
                {
                   "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_b64
                            }
                             
                        },
                        {
                            "type": "text",
                            "text": "이미지에서 문제를 추출해 주세요."
                        }
                    ]
                }
            ]
        )
        return response.content[0].text

    except RateLimitError as e:
        raise RateLimitError(e)
    except Exception as e:
        raise APIRequestError(e)

def retrieve_request(batch_id: str, client: Anthropic) -> MessageBatch:
    '''
    Retrieve the status of batch inference in real-time through MessageBatch object.

    batch_id: id of scheduled batch
    client: service provider; allows retrieving the status
    return MessageBatch object
    '''
    try:
        return client.messages.batches.retrieve(batch_id)
    except Exception as e:
        raise APIRequestError(f"Failed to retrieve batch {batch_id} due to the reason: {e}")

def wait_for_retrieval(batch_id: str, client: Anthropic, timeout_seconds: int = 700, request_interval_seconds: int = 30) -> MessageBatch:
    '''
    Calls retrieve_request until it receives MessageBatch object from service provider that status is "ended". 
    If in progress after timeout_seconds, raise TimeoutError.

    batch_id: id of scheduled batch
    client: service provider
    timeout_seconds: the maximum tolerance on processing time
    request_interval_seconds: The time delay to wait between sending two consecutive requests.
    ''' 
    start = time.time()
    while True:
        batch = retrieve_request(batch_id, client)
        status = getattr(batch, "processing_status", None)
        if status == "ended":
            return batch
        if time.time() - start > timeout_seconds:
            raise TimeoutError(f"It is taking too long for batch to be completed")
        time.sleep(request_interval_seconds)



