import tkinter as tk
from tkinter import ttk, messagebox
from pytubefix import YouTube
from pytubefix.cli import on_progress
import cv2
import os
from reportlab.lib.pagesizes import landscape
from reportlab.pdfgen import canvas
import shutil

# Function to download YouTube video using pytube
def download_video(url, output_path="downloads"):
    yt = YouTube(url, on_progress_callback=on_progress)
    stream = yt.streams.get_highest_resolution()
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    stream.download(output_path)
    return f"{output_path}/{yt.title}.mp4"

# Function to extract frames from the video using OpenCV
def extract_frames(video_path, output_folder="frames", fps=1, progress_var=None, progress_max=None):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    video = cv2.VideoCapture(video_path)
    frame_rate = video.get(cv2.CAP_PROP_FPS)
    frame_interval = int(frame_rate / fps)

    frame_count = 0
    saved_frame_count = 0

    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    if progress_var and progress_max:
        progress_max[0] = total_frames // frame_interval
        progress_var.set(0)

    while video.isOpened():
        ret, frame = video.read()
        if not ret:
            break
        frame_count += 1

        if frame_count % frame_interval == 0:
            frame_filename = f"{output_folder}/frame_{saved_frame_count:04d}.png"
            cv2.imwrite(frame_filename, frame)
            saved_frame_count += 1

            if progress_var:
                progress_var.set(saved_frame_count)

    video.release()

# Function to convert images to PDF
def images_to_pdf(image_folder, output_pdf="output.pdf", progress_var=None):
    c = canvas.Canvas(output_pdf, pagesize=landscape((1280, 720)))
    image_files = sorted([f for f in os.listdir(image_folder) if f.endswith('.png')])

    if progress_var:
        progress_var.set(0)
        progress_var["maximum"] = len(image_files)

    for idx, img_file in enumerate(image_files):
        img_path = os.path.join(image_folder, img_file)
        c.drawImage(img_path, 0, 0, width=1280, height=720)
        c.showPage()

        if progress_var:
            progress_var.set(idx + 1)

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

# Function to handle complete workflow
def convert_video_to_pdf(video_url, progress_var, progress_max):
    try:
        progress_var.set(0)

        # Step 1: Download video
        video_file = download_video(video_url)

        # Step 2: Extract frames with progress
        extract_frames(video_file, progress_var=progress_var, progress_max=progress_max)

        # Step 3: Convert frames to PDF with progress
        images_to_pdf("frames", progress_var=progress_var)

        clean_up()
        messagebox.showinfo("Success", "Video has been converted to PDF successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

# Tkinter UI setup
def main():
    def on_convert_click():
        video_url = url_entry.get()
        if not video_url:
            messagebox.showwarning("Input Error", "Please enter a YouTube URL.")
        else:
            convert_button.config(state=tk.DISABLED)
            progress_var.set(0)
            progress_max[0] = 1  # Reset maximum progress value
            root.update_idletasks()

            try:
                convert_video_to_pdf(video_url, progress_var, progress_max)
            finally:
                convert_button.config(state=tk.NORMAL)

    # Create main window
    root = tk.Tk()
    root.title("YouTube to PDF Converter")

    # Create and place widgets
    tk.Label(root, text="Enter YouTube URL:").pack(pady=10)
    url_entry = tk.Entry(root, width=50)
    url_entry.pack(pady=5)

    progress_var = tk.IntVar()
    progress_max = [1]  # Placeholder for maximum progress

    progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate", variable=progress_var)
    progress_bar.pack(pady=10)

    convert_button = tk.Button(root, text="Convert to PDF", command=on_convert_click)
    convert_button.pack(pady=20)

    # Start the Tkinter event loop
    root.mainloop()

if __name__ == "__main__":
    main()
