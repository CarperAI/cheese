from PIL import Image
import requests
from io import BytesIO

def url2img(url : str, timeout = 1) -> Image:
    """
    Turn URL into PIL image. Can throw a timout error.
    """

    response = requests.get(url, timeout = timeout)
    return Image.open(BytesIO(response.content))
