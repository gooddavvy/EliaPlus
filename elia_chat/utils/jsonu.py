import json
import aiofiles

def json_stringify(data: dict | list) -> str:
    """Convert a dictionary or list to a JSON string."""
    return json.dumps(data, indent=4)

def json_parse(json_string: str):
    """Parse a JSON string to a dictionary, list, etc."""
    return json.loads(json_string)

async def json_parsef(file):
    """Parse a JSON file to a dictionary, list, etc."""
    p = None
    async with aiofiles.open(file, mode='r') as f:
            p = await f.read()
            p = json_parse(p)
    return p