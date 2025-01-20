import requests

def download_file(url, folder, filename):
    """Download a file from the given URL."""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)
    with open(filepath, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"Downloaded: {filepath}")