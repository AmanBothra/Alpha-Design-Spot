import ffmpeg
import urllib.request
import os
from celery import shared_task
import time


@shared_task(bind=True)
def process_video(user_id, video_url, frame_image_url, output_video):
    # Generate the output video filename
    output_video = f"{user_id}_{int(time.time())}_output.mp4"
    print("Video URL (Before urlretrieve):", video_url)
    print("Frame Image URL (Before urlretrieve):", frame_image_url)
    
    # Download the video file
    urllib.request.urlretrieve(video_url, "input.mp4")

    # Download the frame image
    urllib.request.urlretrieve(frame_image_url, "frame.png")

    # Get the video dimensions
    video_info = ffmpeg.probe("input.mp4")
    video_width = int(video_info['streams'][0]['width'])
    video_height = int(video_info['streams'][0]['height'])

    # Get the frame image dimensions
    frame_info = ffmpeg.probe("frame.png")
    frame_width = int(frame_info['streams'][0]['width'])
    frame_height = int(frame_info['streams'][0]['height'])

    # Calculate the scale factor based on the video dimensions
    scale_factor = min(video_width / frame_width, video_height / frame_height)

    # Calculate the frame position
    frame_x = int((video_width - frame_width * scale_factor) / 2)
    frame_y = int((video_height - frame_height * scale_factor) / 2)

    # Add frame to the video using ffmpeg
    ffmpeg.input("input.mp4").output("temp.mp4", vf="movie={},scale={}*iw:{}*ih,format=rgba [watermark]; [in][watermark] overlay={}:{} [out]".format("frame.png", scale_factor, scale_factor, frame_x, frame_y), **{'c:a': 'copy'}).run()

    # Rename the output file to the desired name
    ffmpeg.input("temp.mp4").output(output_video).run()

    # Delete temporary files
    os.remove("input.mp4")
    os.remove("temp.mp4")
    os.remove("frame.png")