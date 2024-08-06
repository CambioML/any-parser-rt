"""AnyParser RT: Real-time parser for any data format."""

import base64
import json
import time
from pathlib import Path
from typing import Tuple

import requests

URL = "https://k7u1c342dc.execute-api.us-west-2.amazonaws.com/v1/extract"
TIMEOUT = 30


class AnyParserRT:
    """AnyParser RT: Real-time parser for any data format."""

    def __init__(self, api_key: str, url: str = URL) -> None:
        """Initialize the AnyParser RT object.

        Args:
            api_key (str): The API key for the AnyParser
            url (str): The URL of the AnyParser RT API.

        Returns:
            None
        """
        self._url = url
        self._api_key = api_key

    def extract(self, file_path: str, extract_args: dict = None) -> Tuple[str, str]:
        """Extract data in real-time.

        Args:
            file_path (str): The path to the file to be parsed.

        Returns:
            tuple(str, str): The extracted data and the time taken.
        """
        file_extension = Path(file_path).suffix.lower().lstrip(".")

        # Check if the file exists
        if not Path(file_path).is_file():
            return "Error: File does not exist", "File does not exist"

        if file_extension in ["pdf", "docx"]:
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

        if extract_args is not None:
            payload["extract_args"] = extract_args

        # Set the headers
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self._api_key,
        }

        # Send the POST request
        start_time = time.time()
        response = requests.post(
            self._url, headers=headers, data=json.dumps(payload), timeout=TIMEOUT
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
