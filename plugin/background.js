chrome.runtime.onInstalled.addListener(() => {
  console.log("Extension installed!");
});

// Listen for messages from the content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "greet") {
    console.log("Message from content script:", message.text);
    sendResponse({ text: "Hello from the background script!" });
  }
});