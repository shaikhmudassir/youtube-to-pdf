from flask import Flask, render_template, request, send_file
from pytubefix import YouTube
from pytubefix.cli import on_progress
import cv2
import os
from reportlab.lib.pagesizes import landscape
from reportlab.pdfgen import canvas
import shutil

app = Flask(__name__)

# Function to download YouTube video using pytube
def download_video(url, resolution, output_path="downloads"):
    yt = YouTube(url, on_progress_callback=on_progress)
    if resolution == "highest":
        stream = yt.streams.get_highest_resolution()
    else:
        stream = yt.streams.filter(res=resolution, progressive=True).first()
        if not stream:
            raise ValueError(f"No stream available for resolution {resolution}")
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    stream.download(output_path)
    return f"{output_path}/{yt.title}.mp4"

# Function to extract frames from the video using OpenCV
def extract_frames(video_path, output_folder="frames", interval_seconds=15):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    video = cv2.VideoCapture(video_path)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = video.get(cv2.CAP_PROP_FPS)  # Frames per second of the video
    interval_frames = int(fps * interval_seconds)  # Calculate frame interval based on 15 seconds

    frame_count = 0
    saved_frame_count = 0

    while video.isOpened():
        ret, frame = video.read()
        if not ret:
            break

        frame_count += 1

        # Capture the first frame at the beginning of the video
        if frame_count == 1:
            frame_filename = f"{output_folder}/frame_{saved_frame_count:04d}.png"
            cv2.imwrite(frame_filename, frame)
            saved_frame_count += 1

        # Capture frame every 15 seconds
        if frame_count % interval_frames == 0:
            frame_filename = f"{output_folder}/frame_{saved_frame_count:04d}.png"
            cv2.imwrite(frame_filename, frame)
            saved_frame_count += 1

    video.release()


# Function to convert images to PDF
def images_to_pdf(image_folder, output_pdf="output.pdf"):
    c = canvas.Canvas(output_pdf, pagesize=landscape((1280, 720)))
    image_files = sorted([f for f in os.listdir(image_folder) if f.endswith('.png')])

    for img_file in image_files:
        img_path = os.path.join(image_folder, img_file)
        c.drawImage(img_path, 0, 0, width=1280, height=720)
        c.showPage()

    c.save()

# Function to clean up directories
def clean_up():
    folders_to_delete = ["downloads", "frames"]

    for folder in folders_to_delete:
        folder_path = os.path.join(os.getcwd(), folder)
        try:
            shutil.rmtree(folder_path)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error deleting folder '{folder}': {e}")

# Route for the home page
@app.route('/')
def home():
    return render_template('index.html')

# Route to handle video to PDF conversion
@app.route('/convert', methods=['POST'])
def convert():
    try:
        video_url = request.form['video_url']
        resolution = request.form.get('resolution', 'highest')
        fps = int(request.form.get('fps', 1))

        if not video_url:
            return "Please provide a YouTube URL", 400

        # Step 1: Download video
        video_file = download_video(video_url, resolution)

        # Step 2: Extract frames from the video
        extract_frames(video_file, interval_seconds=fps)

        # Step 3: Convert extracted frames to PDF
        output_pdf = "output.pdf"
        images_to_pdf("frames", output_pdf)

        # Clean up directories
        clean_up()

        # Send the generated PDF to the user
        return send_file(output_pdf, as_attachment=True)
    except Exception as e:
        print(e)
        return f"An error occurred: {e}", 500

if __name__ == "__main__":
    app.run(debug=True)
