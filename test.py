import requests

file_path = "voice_recording.wav"
server_url = "http://localhost:8000/scramble_full_file"

try:
    with open(file_path, 'rb') as f:
        files = {'file': ('voice_recording.wav', f, 'audio/wav')}
        response = requests.post(server_url, files=files)

    if response.status_code == 200:
        print(response.text)  # Should print "Scrambled audio saved to scrambled_recording.wav"
    else:
        print(f"Error: {response.status_code} - {response.text}")

except FileNotFoundError:
    print(f"File not found: {file_path}")
except requests.exceptions.RequestException as e:
    print(f"Request error: {e}")