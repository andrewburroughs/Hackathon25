import wave
import numpy as np
import matplotlib.pyplot as plt

def load_audio_data(file_path):
    """Loads audio data from a WAV file and returns time and amplitude."""
    try:
        with wave.open(file_path, 'rb') as wf:
            frame_rate = wf.getframerate()
            num_frames = wf.getnframes()
            audio_data = wf.readframes(num_frames)
            num_channels = wf.getnchannels()
            sample_width = wf.getsampwidth()

            # Convert audio data to numerical array (assuming 16-bit PCM)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)

            # If stereo, take only one channel (e.g., the first one)
            if num_channels == 2:
                audio_array = audio_array[::2]

            time = np.linspace(0, len(audio_array) / frame_rate, num=len(audio_array))
            return time, audio_array, frame_rate
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None, None, None
    except wave.Error as e:
        print(f"Error opening or reading WAV file {file_path}: {e}")
        return None, None, None

def visualize_waveforms_with_overlay(file_path1, file_path2):
    """
    Visualizes the waveforms of two audio files and overlays the first on the second (red).

    Args:
        file_path1 (str): Path to the first WAV file.
        file_path2 (str): Path to the second WAV file (will be red).
    """
    time1, audio_array1, rate1 = load_audio_data(file_path1)
    time2, audio_array2, rate2 = load_audio_data(file_path2)

    if time1 is None or time2 is None:
        return

    if rate1 != rate2:
        print("Warning: Frame rates of the two audio files are different. The time axes might not align perfectly.")

    # Ensure both audio arrays have the same length for overlay
    min_len = min(len(audio_array1), len(audio_array2))
    audio_array1 = audio_array1[:min_len]
    audio_array2 = audio_array2[:min_len]
    time = time1[:min_len] # Use time from the first file, assuming similar rates

    # --- Plot the waveforms ---
    plt.figure(figsize=(14, 8))

    plt.subplot(3, 1, 1)
    plt.plot(time, audio_array1)
    plt.title(f'Waveform of {file_path1}')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.grid(True)

    plt.subplot(3, 1, 2)
    plt.plot(time, audio_array2, color='red')
    plt.title(f'Waveform of {file_path2} (Red)')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.grid(True)

    plt.subplot(3, 1, 3)
    plt.plot(time, audio_array1, label=file_path1)
    plt.plot(time, audio_array2, color='red', label=f'{file_path2} (Red)')
    plt.title('Overlay of Waveforms')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    file1 = "voice_recording.wav"  # Replace with the path to your first audio file
    file2 = "scrambled_recording.wav"  # Replace with the path to your second audio file
    visualize_waveforms_with_overlay(file1, file2)