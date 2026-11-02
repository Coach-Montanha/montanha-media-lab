import subprocess
import re
import os

def test_silence_detection():
    # Generate 5s audio: 1s tone, 2s silence, 2s tone
    test_audio = "test_silence_sample.wav"
    cmd_gen = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=1",
        "-f", "lavfi", "-i", "anullsrc=duration=2",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=2",
        "-filter_complex", "[0:a][1:a][2:a]concat=n=3:v=0:a=1[outa]",
        "-map", "[outa]", test_audio
    ]
    subprocess.run(cmd_gen, capture_output=True, check=True)
    
    # Run silencedetect
    cmd_detect = [
        "ffmpeg", "-i", test_audio,
        "-af", "silencedetect=noise=-30dB:d=0.5",
        "-f", "null", "-"
    ]
    res = subprocess.run(cmd_detect, capture_output=True, text=True, encoding="utf-8")
    stderr = res.stderr
    
    silences = []
    # silence_start: 0.999979
    # silence_end: 3.00002 | silence_duration: 2.00004
    start_matches = list(re.finditer(r"silence_start:\s*([\d\.]+)", stderr))
    end_matches = list(re.finditer(r"silence_end:\s*([\d\.]+)\s*\|\s*silence_duration:\s*([\d\.]+)", stderr))
    
    for s, e in zip(start_matches, end_matches):
        silences.append({
            "start": float(s.group(1)),
            "end": float(e.group(1)),
            "duration": float(e.group(2))
        })
        
    print("Detected silences:", silences)
    
    # Translate silences into timeline keep intervals (sound intervals)
    # Total duration = 5.0
    # Keep interval 1: [0.0, silence[0]['start']] -> [0.0, 1.0]
    # (Gap from 1.0 to 3.0 removed)
    # Keep interval 2: [silence[0]['end'], 5.0] -> [3.0, 5.0]
    total_duration = 5.0
    keep_segments = []
    curr = 0.0
    for s in silences:
        if s["start"] > curr:
            keep_segments.append({"start": round(curr, 3), "end": round(s["start"], 3)})
        curr = s["end"]
    if curr < total_duration:
        keep_segments.append({"start": round(curr, 3), "end": round(total_duration, 3)})
        
    print("Keep segments (after trimming silences):", keep_segments)
    
    # Cleanup
    if os.path.exists(test_audio):
        os.remove(test_audio)

if __name__ == "__main__":
    test_silence_detection()
