import json

def load_jsonl(filename: str):
    '''
    Load a JSONL file and return a list of JSON objects.
    '''
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            if not line.strip():
                continue
            yield json.loads(line)
            
def process_batch_output(filename: str) -> None:
    '''
    Process the batch output JSONL file by extracting content (question, answer choices, correct answer) 
    in JSON format and savigng them into a new JSON file.
    '''
    processed_data = []
    questions = {}
    dup = 0
    failure = 0
    for item in load_jsonl(filename):
        try:
            raw_text = item['result']['message']['content'][0]['text']
            obj = json.loads(raw_text)
            if obj['질문'] in questions:
                dup += 1
                continue
            questions[obj['질문']] = 0
            problem_obj = {
                "question": obj['질문'],
                "answer_choices": obj['답변_선택지'],
                "answer": obj['정답']
            }
            processed_data.append(problem_obj)
        except Exception as e:
            print(f"Text missing for item with custom_id: {item.get('custom_id', "undefined")} for reason: {e}")
            failure += 1
            continue
    
    print(f"Total items processed: {len(processed_data) + failure + dup}")
    print(f"Total failures: {failure}")    
    print(f"Total duplicates found: {dup}")
    print(f"Total unique questions processed: {len(questions)}")
        
    with open('data.jsonl', 'w', encoding='utf-8') as file:  
        for data in processed_data:
            json.dump(data, file, ensure_ascii=False)
            file.write('\n')    