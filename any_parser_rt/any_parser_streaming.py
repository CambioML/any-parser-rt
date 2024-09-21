import asyncio
import json
import websockets
import requests
import base64
import json
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

import requests


# TODO: update the endpoint
WS_ENDPOINT = "wss://h00cfygrfi.execute-api.us-west-2.amazonaws.com/dev"
TIMEOUT = 30


class ResultStreaming:
    def __init__(self, ws: websockets) -> None:
        self._ws = ws
        self._closed = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._closed:
            raise StopAsyncIteration

        try:
            response = await self._ws.recv()
            data = json.loads(response)
            # Check FIN
            if data.get("page") == -1:
                if data.get("result") != "DONE":
                    print("Error: Parsing failed.")
                await self._ws.close()
                self._closed = True
                print("Done")
                raise StopAsyncIteration

            return data
        except websockets.ConnectionClosed as e:
            raise StopAsyncIteration from e


class AnyParserStreaming:
    def __init__(self, api_key: str, ws_endpoint: str = WS_ENDPOINT) -> None:
        self._api_key = api_key
        self._ws_endpoint = ws_endpoint

    async def aextract(self, file_path: str, extract_args: Optional[Dict] = None) -> str:
        """Extract data.

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

        if file_extension not in ["pdf", "doc", "docx", "ppt", "pptx"]:
            return "Error: Unsupported file type", "Unsupported file type"

        file_name = Path(file_path).name
        # Create the JSON payload
        payload = {
            "api_key": self._api_key,
            "file_name": file_name,
        }

        if extract_args is not None and isinstance(extract_args, dict):
            payload["extract_args"] = extract_args

        try:
            websocket = await websockets.connect(self._ws_endpoint)
            await websocket.send(json.dumps(payload))

            response = await websocket.recv()
            data = json.loads(response)
            if data.get("error"):
                print(data.get("error"))
                raise Exception(data.get("error"))
            presigned_url = data.get("presignedUrl")
            with open(file_path, "rb") as file_to_upload:
                files = {"file": (file_path.split('/')[-1], file_to_upload)}
                upload_resp = requests.post(
                    presigned_url["url"],
                    data=presigned_url["fields"],
                    files=files,
                    timeout=TIMEOUT,
                )
                if upload_resp.status_code != 204:
                    raise Exception(f"Upload error: {upload_resp.text}")
            
        except json.JSONDecodeError as e:
            raise Exception("Error: Invalid JSON response") from e
        except Exception as e:
            raise Exception("Error request") from e

        return ResultStreaming(websocket)
