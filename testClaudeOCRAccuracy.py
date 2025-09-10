from extractQuestionAnswers import encode_image_to_base64, extract_problem_from_screenshot_one_by_one, APIRequestError, ImageEncodingError
import time
import os
import json
from collections import namedtuple
from dotenv import load_dotenv
from anthropic import Anthropic, RateLimitError

TestPair = namedtuple("TestPair", ["path", "correct_answer"])

TEST_SET = [
    TestPair("Screenshot_20250717_135844_Samsung Internet.jpg", 1),
    TestPair("Screenshot_20250717_140008_Samsung Internet.jpg", 2),
    TestPair("Screenshot_20250717_140209_Samsung Internet.jpg", 3),
    TestPair("Screenshot_20250717_140259_Samsung Internet.jpg", 3),
    TestPair("Screenshot_20250717_142158_Samsung Internet.jpg", 3),
    TestPair("Screenshot_20250717_142227_Samsung Internet.jpg", 1),
    TestPair("Screenshot_20250717_142415_Samsung Internet.jpg", 2),
]

def test_ClaudeOCR_correct_answer_detection_accuracy(directory: str) -> None:
    '''Test the accuracy of Claude OCR in extracting correct answers from screenshots.'''
    load_dotenv()
    client = Anthropic(api_key=os.getenv("API_KEY"))
    correct_answer_count = 0

    def test_individual_pair(pair):
        nonlocal correct_answer_count

        full_path = directory + pair.path

        try:
            image_b64 = encode_image_to_base64(full_path)
        except ImageEncodingError as e:
            print(f"ImageEncodingError: {e}")
        
        try:
            problem_str = extract_problem_from_screenshot_one_by_one(image_b64, client)
        except RateLimitError as e:
            raise RateLimitError(e) 
        except APIRequestError as e:
            raise APIRequestError(e)

        try:
            problem_json = json.loads(problem_str)
        except Exception as e:
            raise APIRequestError(f"Unexpected file format: {problem_str} due to that {e}")
        
        if problem_json["정답"] == pair.correct_answer:
            correct_answer_count += 1
        print(f"Problem: {problem_json}")
    
    MAX_RETRIES = 3
    for pair in TEST_SET:
        success = False
        for _ in range(MAX_RETRIES):
            try:
                test_individual_pair(pair)
                success = True
                break
            except RateLimitError as e:
                time.sleep(10)
                continue
            except Exception as e:
                print(f"Unexpected Error occurred: {e}")
                success = False
                break
        if not success:
            continue
    
    total_count = len(TEST_SET)
    accuracy = correct_answer_count / total_count
    print(f"Accuracy: {accuracy:.3f} ({correct_answer_count} / {total_count})")

test_ClaudeOCR_correct_answer_detection_accuracy("/Volumes/Seagate Portable Drive/")

#Claude-Sonnet-4-20250514 achieved 100% accuracy.
#TO-DO: Need to add more test cases.