import random
from moviepy.editor import VideoFileClip, concatenate_videoclips
from googleapiclient.discovery import build
import yt_dlp
import os
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

# YouTube API search function
def search_youtube(query, max_results=5):
    api_key = "AIzaSyCU8JZZ88PS62pmnQqV_7tgBuf9cWOh9d8"  # Replace with your YouTube Data API key
    youtube = build("youtube", "v3", developerKey=api_key)

    request = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=max_results
    )
    response = request.execute()
    
    # Extract video IDs and titles from the response
    return [(item['id']['videoId'], item['snippet']['title']) for item in response['items']]

# YouTube video download function with retry logic
def download_youtube_video(video_id, retries=3):
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  # Ensure best video with audio
        'outtmpl': f'{video_id}.%(ext)s',  # Output template with extension
        'merge_output_format': 'mp4'  # Ensure audio and video are merged into mp4
    }
    
    for attempt in range(retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                return f"{video_id}.mp4"
        except Exception as e:
            print(f"Attempt {attempt + 1} of {retries} failed: {e}")
            if attempt + 1 == retries:
                print(f"Failed to download video {video_id} after {retries} attempts.")
                return None

# Clip extraction function
def create_compilation(search_phrase, num_clips=5, clip_duration=10):
    results = search_youtube(search_phrase, max_results=10)
    clips = []

    if not results:
        print("No results found.")
        return

    # Process each YouTube video
    for video_id, title in random.sample(results, min(num_clips, len(results))):
        print(f"Processing: {title}")
        
        video_file = download_youtube_video(video_id)
        if video_file:
            try:
                # Load the video clip
                video_clip = VideoFileClip(video_file)
                
                # Check if the video has audio
                if video_clip.audio is None:
                    print(f"No audio found in video {title}, skipping.")
                    continue
                
                # Extract random clip from the video
                start_time = random.randint(0, max(0, int(video_clip.duration - clip_duration)))
                clip = video_clip.subclip(start_time, start_time + clip_duration)
                
                # Save trimmed clip with audio
                trimmed_file = f"trimmed_{video_id}.mp4"
                clip.write_videofile(trimmed_file, codec="libx264", audio_codec="aac")  # Ensure audio is included
                
                clips.append(VideoFileClip(trimmed_file))

                # Clean up original video file
                video_clip.close()
                os.remove(video_file)
            except Exception as e:
                print(f"Error processing video {video_file}: {e}")
                continue

    # Concatenate all clips if there are any
    if clips:
        try:
            # Use method="compose" to ensure audio is handled properly
            final_clip = concatenate_videoclips(clips, method="compose")
            final_clip.write_videofile("compilation.mp4", codec="libx264", audio_codec="aac")  # Ensure audio is included
            print("Compilation created successfully!")
        except Exception as e:
            print(f"Error creating final compilation: {e}")
    else:
        print("No suitable clips found.")

# Example usage
search_phrase = input("Enter the search phrase: ")  # User inputs the search phrase in the terminal
create_compilation(search_phrase, num_clips=3, clip_duration=15)
