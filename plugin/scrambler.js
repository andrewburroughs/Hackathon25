console.log("Scrambler AudioWorkletProcessor loaded");

class ScramblerProcessor extends AudioWorkletProcessor {
  process(inputs, outputs) {
    const input = inputs[0];
    const output = outputs[0];

    if (input && input[0]) {
      const inputChannel = input[0];
      const outputChannel = output[0];

      // Add random noise to the audio samples
      for (let i = 0; i < inputChannel.length; i++) {
        //const noise = (Math.random() * 0.2 - 0.1); // Random noise between -0.1 and 0.1
        outputChannel[i] = -inputChannel[i]; // Add noise to the audio sample
      }
    }
    console.log("Scrambler AudioWorkletProcessor loaded");

    return true; // Keep the processor alive
  }
}

registerProcessor('scrambler', ScramblerProcessor);