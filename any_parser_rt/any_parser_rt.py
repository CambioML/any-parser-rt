"""AnyParser RT: Real-time parser for any data format."""

import base64
import json
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

import requests

PUBLIC_SHARED_BASE_URL = "https://api.cambio-ai.com"
TIMEOUT = 30


class AnyParserRT:
    """AnyParser RT: Real-time parser for any data format."""

    def __init__(self, api_key: str, base_url: str = PUBLIC_SHARED_BASE_URL) -> None:
        """Initialize the AnyParser RT object.

        Args:
            api_key (str): The API key for the AnyParser
            url (str): The URL of the AnyParser RT API.

        Returns:
            None
        """
        self._sync_url = f"{base_url}/extract"
        self._async_upload_url = f"{base_url}/async/upload"
        self._async_fetch_url = f"{base_url}/async/fetch"
        self._api_key = api_key

    def extract(
        self, file_path: str, extract_args: Optional[Dict] = None
    ) -> Tuple[str, str]:
        """Extract data in real-time.

        Args:
            file_path (str): The path to the file to be parsed.
            extract_args (Optional[Dict]): Additional extraction arguments added to prompt
        Returns:
            tuple(str, str): The extracted data and the time taken.
        """
        file_extension = Path(file_path).suffix.lower().lstrip(".")

        # Check if the file exists
        if not Path(file_path).is_file():
            return "Error: File does not exist", "File does not exist"

        if file_extension in ["pdf", "doc", "docx", "ppt", "pptx", "jpg", "jpeg", "png", "gif"]:
            # Encode the PDF file content in base64
            with open(file_path, "rb") as file:
                encoded_file = base64.b64encode(file.read()).decode("utf-8")
        else:
            return "Error: Unsupported file type", "Unsupported file type"

        # Create the JSON payload
        payload = {
            "file_content": encoded_file,
            "file_type": file_extension,
        }

        if extract_args is not None and isinstance(extract_args, dict):
            payload["extract_args"] = extract_args

        # Set the headers
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self._api_key,
        }

        # Send the POST request
        start_time = time.time()
        response = requests.post(
            self._sync_url, headers=headers, data=json.dumps(payload), timeout=TIMEOUT
        )
        end_time = time.time()

        # Check if the request was successful
        if response.status_code == 200:
            try:
                response_data = response.json()
                response_list = []
                for text in response_data["markdown"]:
                    response_list.append(text)
                markdown_text = "\n".join(response_list)
                return (
                    markdown_text,
                    f"Time Elapsed: {end_time - start_time:.2f} seconds",
                )
            except json.JSONDecodeError:
                return "Error: Invalid JSON response", f"Response: {response.text}"
        else:
            return f"Error: {response.status_code}", f"Response: {response.text}"

    def async_extract(self, file_path: str, extract_args: Optional[Dict] = None) -> str:
        """Extract data asyncronously.

        Args:
            file_path (str): The path to the file to be parsed.
            extract_args (Optional[Dict]): Additional extraction arguments added to prompt
        Returns:
            str: The file id of the uploaded file.
        """
        file_extension = Path(file_path).suffix.lower().lstrip(".")

        # Check if the file exists
        if not Path(file_path).is_file():
            return "Error: File does not exist", "File does not exist"

        if file_extension not in ["pdf", "doc", "docx", "ppt", "pptx", "jpg", "jpeg", "png", "gif"]:
            return "Error: Unsupported file type", "Unsupported file type"

        file_name = Path(file_path).name
        # Create the JSON payload
        payload = {
            "file_name": file_name,
        }

        if extract_args is not None and isinstance(extract_args, dict):
            payload["extract_args"] = extract_args

        # Set the headers
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self._api_key,
        }

        # Send the POST request
        response = requests.post(
            self._async_upload_url,
            headers=headers,
            data=json.dumps(payload),
            timeout=TIMEOUT,
        )

        # Check if the request was successful
        if response.status_code == 200:
            try:
                file_id = response.json().get("fileId")
                presigned_url = response.json().get("presignedUrl")
                with open(file_path, "rb") as file_to_upload:
                    files = {"file": (file_path, file_to_upload)}
                    upload_resp = requests.post(
                        presigned_url["url"],
                        data=presigned_url["fields"],
                        files=files,
                        timeout=TIMEOUT,
                    )
                    if upload_resp.status_code != 204:
                        return f"Upload error: {upload_resp}"
                return file_id
            except json.JSONDecodeError:
                return "Error: Invalid JSON response"
        else:
            return f"Request error: {response}"

    def async_fetch(
        self,
        file_id: str,
        sync: bool = True,
        sync_timeout: int = 60,
        sync_interval: int = 5,
    ) -> str:
        response = None
        # Create the JSON payload
        payload = {"file_id": file_id}
        # Set the headers
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self._api_key,
        }
        if sync:
            start_time = time.time()
            while time.time() < start_time + sync_timeout:
                response = requests.post(
                    self._async_fetch_url,
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=TIMEOUT,
                )
                if response.status_code == 202:
                    print("Waiting for response...")
                    time.sleep(sync_interval)
                    continue
                break
        else:
            response = requests.post(
                self._async_fetch_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=TIMEOUT,
            )

        if response is None:
            return "Error: timeout, no response received"
        elif response.status_code == 200:
            markdown_list = response.json()["markdown"]
            return "\n".join(markdown_list)
        elif response.status_code == 202:
            return None
        return f"Error: {response.status_code}"
