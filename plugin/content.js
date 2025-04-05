// Send a message to the background script
chrome.runtime.sendMessage({ type: "greet", text: "Hello from the content script!" }, (response) => {
  console.log("Response from background script:", response.text);
});

// Modify the current page (example: change the background color)
document.body.style.backgroundColor = "lightblue";