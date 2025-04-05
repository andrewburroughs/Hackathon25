import pyaudio
import numpy as np
import random

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 48000

p = pyaudio.PyAudio()

# --- Modulation Settings ---
min_pitch_factor_low = 0.6
max_pitch_factor_low = 0.8
min_pitch_factor_high = 1.2
max_pitch_factor_high = 1.5
change_probability = 0.7
change_frequency_factor = 5

audio_chunk_counter = 0
# Initialize with a random modulating pitch factor
if random.random() < 0.5:
    current_pitch_factor = random.uniform(min_pitch_factor_low, max_pitch_factor_low)
else:
    current_pitch_factor = random.uniform(min_pitch_factor_high, max_pitch_factor_high)

try:
    input_stream = p.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            frames_per_buffer=CHUNK)

    output_stream = p.open(format=FORMAT,
                             channels=CHANNELS,
                             rate=RATE,
                             output=True)

    print("Listening for audio... Press Ctrl+C to stop.")

    while True:
        data = input_stream.read(CHUNK)
        audio_array = np.frombuffer(data, dtype=np.int16)

        # --- Random Pitch Modulation ---
        if audio_chunk_counter % change_frequency_factor == 0:
            if random.random() < change_probability:
                if random.random() < 0.5:
                    current_pitch_factor = random.uniform(min_pitch_factor_low, max_pitch_factor_low)
                else:
                    current_pitch_factor = random.uniform(min_pitch_factor_high, max_pitch_factor_high)
            # Removed the else condition that set current_pitch_factor to 1.0

        pitch_factor = current_pitch_factor

        if pitch_factor > 1.0:
            new_length = int(len(audio_array) / pitch_factor)
            if new_length > 0:
                indices = np.round(np.linspace(0, len(audio_array) - 1, new_length)).astype(int)
                modulated_audio = audio_array[indices]
            else:
                modulated_audio = np.array([], dtype=np.int16)
        elif pitch_factor < 1.0:
            repeat_factor = int(1 / pitch_factor)
            modulated_audio = np.repeat(audio_array, repeat_factor)[:len(audio_array)]
        else:
            modulated_audio = audio_array

        # Ensure the output data has the correct length
        output_chunk_size_samples = CHUNK * CHANNELS
        if len(modulated_audio) < output_chunk_size_samples:
            padding = np.zeros(output_chunk_size_samples - len(modulated_audio), dtype=np.int16)
            modulated_audio = np.concatenate((modulated_audio, padding))
        elif len(modulated_audio) > output_chunk_size_samples:
            modulated_audio = modulated_audio[:output_chunk_size_samples]

        modified_data = modulated_audio.tobytes()
        output_stream.write(modified_data)

        audio_chunk_counter += 1

except KeyboardInterrupt:
    print("\nStopping...")
except Exception as e:
    print(f"An error occurred: {e}")

finally:
    input_stream.stop_stream()
    input_stream.close()
    output_stream.stop_stream()
    output_stream.close()
    p.terminate()