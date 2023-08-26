import os
import uuid
from io import BytesIO
from uuid import uuid4

import ffmpeg
from PIL import Image
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible


@deconstructible
class rename_file_name(object):

    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        # set filename as random string
        filename = '{}.{}'.format(uuid4().hex, ext)
        # return the whole path to the file
        return os.path.join(self.path, filename)


def get_image_file_extension_validator():
    return [
        FileExtensionValidator(allowed_extensions=["svg", "png", "jpg", "jpeg", "webp"])
    ]


def file_size(value):
    """
        Same as FileField, but you can specify:
            2.5MB - 2621440
            5MB - 5242880
            10MB - 10485760
            20MB - 20971520
            50MB - 5242880
            100MB - 104857600
            250MB - 214958080
            500MB - 429916160
    """
    limit = 5242880
    if value.size > limit:
        raise ValidationError("File too large. Size should not exceed 5 MB.")


def file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = [".pdf", ".doc", ".docx"]
    if not ext in valid_extensions:
        raise ValidationError(
            "Unsupported file type. Only Pdf and MsWord files are allowed."
        )


def converter_to_webp(image_instance):
    """
    Convert any image object to WebP for faster image load time.
    """
    if image_instance:
        image_file_format = ["png", "jpeg", "jpg", "jpe", "rgba", "rgb", "bmp", "webp"]
        ext = image_instance.name.split(".")[-1].lower()

        if ext in image_file_format:
            image = Image.open(image_instance)
            image_io = BytesIO()
            image.save(image_io, format="WEBP", quality=80)
            image_instance.save(image_instance.name.split(".")[0] + ".webp", ContentFile(image_io.getvalue()),
                                save=False)


def generate_video_with_frame(customer_frame, post):
    # Get the paths of the frame image and video from the CustomerFrame and Post objects
    frame_image_path = customer_frame.frame_img.path
    video_path = post.file.path

    # Create the 'video-with-frame' directory inside MEDIA_ROOT if it doesn't exist
    media_directory = os.path.join(settings.MEDIA_ROOT, 'video-with-frame')
    os.makedirs(media_directory, exist_ok=True)

    # Output video file name
    # Generate a unique ID using UUID
    unique_id = str(uuid.uuid4())
    output_video = f"output_{unique_id}.mp4"

    # Get the video dimensions
    video_info = ffmpeg.probe(video_path)
    video_width = int(video_info['streams'][0]['width'])
    video_height = int(video_info['streams'][0]['height'])

    # Get the frame image dimensions
    frame_info = ffmpeg.probe(frame_image_path)
    frame_width = int(frame_info['streams'][0]['width'])
    frame_height = int(frame_info['streams'][0]['height'])

    # Calculate the scale factor based on the video dimensions
    scale_factor = min(video_width / frame_width, video_height / frame_height)

    # Calculate the frame position
    frame_x = int((video_width - frame_width * scale_factor) / 2)
    frame_y = int((video_height - frame_height * scale_factor) / 2)

    # Add frame to the video using ffmpeg
    ffmpeg.input(video_path).output(os.path.join(media_directory, output_video),
                                    vf="movie={},scale={}*iw:{}*ih,format=rgba [watermark]; [in][watermark] overlay={}:{} [out]".format(
                                        frame_image_path, scale_factor, scale_factor, frame_x, frame_y),
                                    **{'c:a': 'copy'}).run()

    # Get the full media URL for the output video
    output_video_url = os.path.join(settings.MEDIA_URL, 'video-with-frame', output_video)

    return output_video_url
