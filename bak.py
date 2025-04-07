import time
import requests

def make_request_with_retry(url, retries=5, backoff=2):
    for i in range(retries):
        response = requests.get(url)
        if response.status_code == 503:
            wait_time = backoff ** i
            print(f"503 received. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        else:
            return response
    return None
