class ScramblerProcessor extends AudioWorkletProcessor {
  // Process audio data
  process(inputs, outputs) {
    const input = inputs[0]; 
    const output = outputs[0];

    if (input && input[0]) {
      const inputChannel = input[0]; 
      const outputChannel = output[0];

      // Add random noise to the audio samples
      for (let i = 0; i < inputChannel.length; i++) {
        const noise = (Math.random() * 0.2 - 0.1); 
        outputChannel[i] = inputChannel[i] + noise;
      }
    }

    return true; // Keep the processor alive
  }
}

// Register the processor
registerProcessor('scrambler', ScramblerProcessor);