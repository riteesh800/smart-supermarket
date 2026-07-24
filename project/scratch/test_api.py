import requests
import json
import os

BASE_URL = "http://localhost:8000/api/upload"
CSV_PATH = r"C:\Users\netca\.gemini\antigravity-ide\brain\6f09287e-e550-4537-a18a-2029b17a72b5\scratch\test_no_timestamp.csv"

def test_upload():
    print("1. Resetting database...")
    res = requests.post(f"{BASE_URL}/reset")
    print("Reset response:", res.json())

    print("\n2. Uploading CSV for preview...")
    with open(CSV_PATH, "rb") as f:
        files = {"file": ("test_no_timestamp.csv", f, "text/csv")}
        res = requests.post(f"{BASE_URL}/preview", files=files)
    
    preview_data = res.json()
    print("Preview response summary:")
    print("upload_id:", preview_data.get("upload_id"))
    print("detected_type:", preview_data.get("detected_type"))
    print("detected_mapping:", preview_data.get("detected_mapping"))

    upload_id = preview_data.get("upload_id")
    detected_mapping = preview_data.get("detected_mapping")

    print("\n3. Importing data with detected mapping...")
    data = {
        "upload_id": upload_id,
        "file_type": "sales",
        "mapping_json": json.dumps(detected_mapping)
    }
    res = requests.post(f"{BASE_URL}/import", data=data)
    print("Import response status code:", res.status_code)
    try:
        import_res = res.json()
        print("Import response:", json.dumps(import_res, indent=2))
    except Exception as e:
        print("Failed to decode JSON response:", res.text)
        return

    print("\n4. Getting system status...")
    res = requests.get(f"{BASE_URL}/status")
    print("Status response:", json.dumps(res.json(), indent=2))

if __name__ == "__main__":
    test_upload()
