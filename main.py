from extractQuestionAnswers import create_request, wait_for_retrieval, extract_problem_from_screenshot_on_batch
from measureRequestByteSize import measure_request_byte_size
from retrievePaths import retrieve_paths
from dotenv import load_dotenv
import os
from anthropic import Anthropic
from processBatchOutput import process_batch_output

def main():
    '''Main function to execute the problem extraction process.'''
    load_dotenv()
    client = Anthropic(api_key = os.getenv("API_KEY")) 
    directory = os.getenv("DIRECTORY")
    
    #Retrieve valid JPG image file paths from the specified local directory
    paths = retrieve_paths(directory)

    # Create a batch request
    batch_request = create_request(paths)
    
    #measure the byte size of the request (limit for claude batch request is 256MB (= 256000000 bytes))
    byte_size = measure_request_byte_size(batch_request)
    print(f"Request byte size: {byte_size} bytes")
    
    try:
        batch_message = extract_problem_from_screenshot_on_batch(batch_request, client)
        print(f"Batch ID: {batch_message.id} was successfully created.")
    except Exception as e:
        print(f"Batch request failed: {e}")
        return
    
    # Wait for the batch to be processed
    try:
        _ = wait_for_retrieval(batch_message.id, client)
        print("Batch processing completed.")
    except:
        print("Error during batch processing.")
    process_batch_output("problems.jsonl")
        
if __name__ == "__main__":
    main()