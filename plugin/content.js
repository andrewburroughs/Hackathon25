// Send a message to the background script
browser.runtime.sendMessage({ type: "greet", text: "Hello from the content script!" })
  .then((response) => {
    console.log("Response from background script:", response.text);
  })
  .catch((error) => {
    console.error("Error sending message to background script:", error);
  });

// Save the original getUserMedia function
const originalGetUserMedia = navigator.mediaDevices.getUserMedia;

// Override the getUserMedia function
navigator.mediaDevices.getUserMedia = function (constraints) {
  console.log("Website is requesting access to camera/microphone:", constraints);

  if (constraints.audio) {
    return originalGetUserMedia.call(navigator.mediaDevices, constraints)
      .then((stream) => {
        console.log("Original microphone stream intercepted");

        // Create an AudioContext
        const audioContext = new AudioContext();

        // Add the AudioWorkletProcessor
        return audioContext.audioWorklet.addModule('scrambler.js').then(() => {
          const source = audioContext.createMediaStreamSource(stream);
          const scramblerNode = new AudioWorkletNode(audioContext, 'scrambler');
          const destination = audioContext.createMediaStreamDestination();

          // Connect the nodes
          source.connect(scramblerNode);
          scramblerNode.connect(destination);

          // Create a new MediaStream with the scrambled audio
          const scrambledStream = destination.stream;

          console.log("Returning scrambled microphone stream to the website");
          return scrambledStream; // Return the scrambled stream to the website
        });
      })
      .catch((error) => {
        console.error("Error accessing microphone:", error);
        throw error;
      });
  }

  // If no audio is requested, call the original getUserMedia
  return originalGetUserMedia.call(navigator.mediaDevices, constraints);
};