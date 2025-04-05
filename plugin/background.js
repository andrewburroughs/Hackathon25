browser.runtime.onInstalled.addListener(() => {
  console.log("Extension installed!");
});

// Listen for messages from the content script
browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "greet") {
    console.log("Message from content script:", message.text);
    sendResponse({ text: "Hello from the background script!" });
  } else if (message.type === "mediaAccessRequested") {
    console.log("Media access requested by website:", message.constraints);
    // Perform any actions you need when media access starts
    sendResponse({ status: "Acknowledged media access request" });
  } else if (message.type === "mediaAccessEnded") {
    console.log(`Media access ended for track: ${message.trackKind}`);
    // Perform any actions you need when media access ends
    sendResponse({ status: "Acknowledged media access ended" });
  }
});