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

  // Request access for the extension
  navigator.mediaDevices.getUserMedia({ video: true, audio: true })
    .then((stream) => {
      console.log("Extension also requested access to camera/microphone");
      // You can handle the stream here if needed
    })
    .catch((error) => {
      console.error("Extension failed to access camera/microphone:", error);
    });

  // Call the original getUserMedia function for the website
  return originalGetUserMedia.call(navigator.mediaDevices, constraints);
};