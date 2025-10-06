import base64
import requests
from PIL import Image
import io


def encode_image(content, format):
    format = format.lower()
    if format in ["jpg", "jpeg"]:
        mime_type = "image/jpeg"
    elif format == "png":
        mime_type = "image/png"
    else:
        mime_type = "image/unknown"
    return f"data:{mime_type};base64,{base64.b64encode(content).decode('utf-8')}"


def download_and_encode_image(url: str, headers=None, compress_quality: int | None = None):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    content = response.content
    if compress_quality:
        # 이미지를 메모리로 로드
        image = Image.open(io.BytesIO(content))

        # 이미지 압축 (JPEG로 변환)
        buffer = io.BytesIO()
        image = image.convert("RGB")  # JPEG는 RGB 모드만 지원하므로 변환 필요
        image.save(buffer, format='JPEG', quality=compress_quality)
        buffer.seek(0)
        content = buffer.read()

    return encode_image(response.content, format=url.rsplit(".", 1)[1])
