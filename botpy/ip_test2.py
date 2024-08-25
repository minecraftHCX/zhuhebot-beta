import requests

def access_url(url):
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error accessing {url}: {e}")

if __name__ == "__main__":
    # 指定要访问的URL
    target_url = "http://localhost:8080"
    access_url(target_url)
