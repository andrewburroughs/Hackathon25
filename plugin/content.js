// Compatibility layer for Chrome
if (typeof browser === "undefined") {
  var browser = chrome;
}

browser.storage.local.clear()

// Send a message to the background script
browser.runtime.sendMessage({ type: "greet", text: "Hello from the content script!" })
  .then((response) => {
    console.log("Response from background script:", response.text);
  })
  .catch((error) => {
    console.error("Error sending message to background script:", error);
  });

// Permissions to check
const permissions = ["camera", "microphone"];

// Process permissions and save their states
processPermissions();

async function processPermissions() {
  for (const permission of permissions) {
    const storedState = await getStoredPermissionState(permission);

    // If permission is already granted, skip querying
    if (storedState === "granted") {
      console.log(`${permission} is already granted. Skipping query.`);
      continue;
    }

    // Query the permission state
    const result = await getPermission(permission);
    console.log(`${permission}: ${result}`);

    // Save the permission state in storage
    savePermissionState(permission, result);

    // If permission is denied, listen for changes to re-request access
    if (result === "denied") {
      listenForPermissionChanges(permission);
    }
  }
}

// Query a single permission and return its state
async function getPermission(permission) {
  try {
    const result = await navigator.permissions.query({ name: permission });
    return result.state; // Return the state directly (e.g., "granted", "denied", "prompt")
  } catch (error) {
    console.error(`Error querying permission for ${permission}:`, error);
    return "not supported";
  }
}

// Save the permission state in storage
function savePermissionState(permission, state) {
  const permissionData = { [permission]: state };
  browser.storage.local.set(permissionData, () => {
    console.log(`Saved permission state for ${permission}:`, state);
  });
}

// Load a specific permission state from storage
function getStoredPermissionState(permission) {
  return new Promise((resolve) => {
    browser.storage.local.get(permission, (result) => {
      resolve(result[permission] || null); // Return the stored state or null if not found
    });
  });
}

// Listen for permission state changes and re-request access if denied
function listenForPermissionChanges(permission) {
  navigator.permissions.query({ name: permission }).then((permissionStatus) => {
    permissionStatus.onchange = async () => {
      console.log(`Permission state for ${permission} changed to: ${permissionStatus.state}`);

      if (permissionStatus.state === "denied") {
        console.log(`Re-requesting access for ${permission}`);
        try {
          const constraints = permission === "camera" ? { video: true } : { audio: true };
          const stream = await navigator.mediaDevices.getUserMedia(constraints);
          console.log(`Access granted for ${permission} after re-request.`);
        } catch (error) {
          console.error(`Error re-requesting access for ${permission}:`, error);
        }
      }
    };
  });
}

// Load all saved permissions from storage (for debugging or initialization)
function loadPermissions() {
  browser.storage.local.get(permissions, (result) => {
    console.log("Loaded permissions from storage:", result);
  });
}

// Call this function to load permissions when needed
loadPermissions();

// Save the original getUserMedia function
const originalGetUserMedia = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);

// Declare the AudioContext globally
let audioContext;

// Function to initialize or resume the AudioContext
const initializeAudioContext = () => {
  if (!audioContext) {
    audioContext = new AudioContext();
    console.log("AudioContext created after user gesture");

    // Generate silent audio to unlock the AudioContext
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    gainNode.gain.value = 0; // Set volume to 0 (silent)
    oscillator.connect(gainNode).connect(audioContext.destination);
    oscillator.start();
    oscillator.stop(audioContext.currentTime + 0.1); // Play for 0.1 seconds
  }

  if (audioContext.state === "suspended") {
    audioContext.resume().then(() => {
      console.log("AudioContext resumed after user gesture");
    }).catch((error) => {
      console.error("Failed to resume AudioContext:", error);
    });
  }
};

// Ensure the AudioContext is ready before proceeding
const ensureAudioContextReady = async () => {
  if (!audioContext || audioContext.state === "suspended") {
    console.log("Waiting for AudioContext to be ready...");
    await initializeAudioContext();
  }
};

// Declare scrambledStream in a wider scope
let scrambledStream;

// Create a WeakMap to store the original stream
const streamMap = new WeakMap();

// Override the getUserMedia function globally
navigator.mediaDevices.getUserMedia = async function (constraints) {
  console.log("Website is requesting access to camera/microphone:", constraints);

  try {
    // Ensure the AudioContext is ready
    await ensureAudioContextReady();

    if (constraints.audio) {
      return originalGetUserMedia(constraints)
        .then(async (stream) => {
          console.log("Original microphone stream intercepted");

          // Store the original stream in the WeakMap
          streamMap.set(stream, stream);

          // Add the AudioWorkletProcessor
          try {
            await audioContext.audioWorklet.addModule(browser.runtime.getURL('scrambler.js'));
          } catch (error) {
            console.error("Error adding AudioWorkletModule:", err);
            throw error;
          }

          const source = audioContext.createMediaStreamSource(stream);
          const scramblerNode = new AudioWorkletNode(audioContext, 'scrambler');
          const destination = audioContext.createMediaStreamDestination();

          // Connect the nodes
          source.connect(scramblerNode);
          console.log("Connected source to scramblerNode");
          scramblerNode.connect(destination);
          console.log("Connected scramblerNode to destination");

          // Log the state of the AudioContext
          console.log("AudioContext state:", audioContext.state);

          // Create a new MediaStream with the scrambled audio
          scrambledStream = destination.stream; // Assign to the global variable

          // Inspect the MediaStream
          console.log("Original Stream:", stream);
          console.log("Scrambled Stream:", scrambledStream);

          // Get the audio tracks
          const audioTracks = scrambledStream.getAudioTracks();
          console.log("Number of audio tracks in scrambled stream:", audioTracks.length);

          // Check if there are any tracks
          if (audioTracks.length > 0) {
            console.log("Audio track kind:", audioTracks[0].kind);
            console.log("Audio track state:", audioTracks[0].readyState);
          }

          // Revoke the original stream's tracks
          stream.getTracks().forEach(track => track.stop());

          console.log("Returning scrambled microphone stream to the website");
          return scrambledStream;
        })
        .catch((error) => {
          console.error("Error accessing microphone:", error);
          throw error;
        });
    }

    // If no audio is requested, call the original getUserMedia
    return originalGetUserMedia(constraints);
  } catch (error) {
    console.error("Error in overridden getUserMedia:", error);
    throw error;
  }
};

// 1. Store the original method
const originalSetSrcObject = Object.getOwnPropertyDescriptor(HTMLMediaElement.prototype, 'srcObject').set;

// 2. Define our proxy
function proxiedSetSrcObject(stream) {
  console.log("setSrcObject called with:", stream);

  if (stream instanceof MediaStream) {
    console.log("Replacing with scrambled stream");
    stream = scrambledStream; // Assuming scrambledStream is in scope
  }

  // 3. Call the original method
  return originalSetSrcObject.apply(this, [stream]);
}

// 4. Override the original
Object.defineProperty(HTMLMediaElement.prototype, 'srcObject', {
  set: proxiedSetSrcObject
});

// Create a MutationObserver
const observer = new MutationObserver(function(mutations) {
  mutations.forEach(function(mutation) {
    if (mutation.type === 'attributes' && mutation.attributeName === 'srcObject') {
      const element = mutation.target;
      if (element instanceof HTMLMediaElement && element.srcObject instanceof MediaStream) {
        console.log('Website is setting srcObject:', element.srcObject);
        // Replace the original stream with the scrambled stream
        element.srcObject = scrambledStream; // Assuming scrambledStream is in scope
        console.log('Replacing with scrambled stream:', element.srcObject);
      }
    }
  });
});

// Start observing the document
observer.observe(document, {
  attributes: true,
  childList: true,
  subtree: true
});

// Initialize the AudioContext on user gesture
document.addEventListener("click", initializeAudioContext);
document.addEventListener("keydown", initializeAudioContext);
document.addEventListener("touchstart", initializeAudioContext);

// Test the overridden getUserMedia function
navigator.mediaDevices.getUserMedia({ audio: true })
  .then((stream) => {
    console.log("Microphone access granted and scrambled stream returned");
  })
  .catch((error) => {
    console.error("Error accessing microphone:", error);
  });

// Store the original getTracks method
const originalGetTracks = MediaStream.prototype.getTracks;

// Override the getTracks method
MediaStream.prototype.getTracks = function() {
  console.log("getTracks called on:", this);
  const originalStream = streamMap.get(this);
  if (originalStream) {
    console.log("Blocking access to original stream's tracks");
    return []; // Return an empty array
  }
  return originalGetTracks.apply(this, arguments);
};

// Listen for messages from the website
window.addEventListener('message', function(event) {
    if (event.data.type === 'REQUEST_SCRAMBLED_STREAM') {
        console.log("Website requested scrambled stream. Sending stream.");
        window.postMessage({ type: 'SCRAMBLED_STREAM', stream: scrambledStream }, '*');
    }
});

// Inject a script into the web page to expose the scrambledStream
const script = document.createElement('script');
script.textContent = `
  (function() {
    let scrambledStream;

    // Override navigator.mediaDevices.getUserMedia
    const originalGetUserMedia = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
    navigator.mediaDevices.getUserMedia = async function(constraints) {
      if (constraints.audio) {
        if (!scrambledStream) {
          console.log("Creating scrambled stream in the web page context.");
          const originalStream = await originalGetUserMedia(constraints);

          // Create an AudioContext and scramble the audio
          const audioContext = new AudioContext();
          const source = audioContext.createMediaStreamSource(originalStream);
          const destination = audioContext.createMediaStreamDestination();

          // Add a simple gain node or any other processing node here
          const gainNode = audioContext.createGain();
          gainNode.gain.value = 0.5; // Example: Reduce volume by 50%
          source.connect(gainNode).connect(destination);

          scrambledStream = destination.stream;
        }
        return scrambledStream;
      }
      return originalGetUserMedia(constraints);
    };

    // Expose a function to request the scrambled stream
    window.requestScrambledStream = async function() {
      return navigator.mediaDevices.getUserMedia({ audio: true });
    };
  })();
`;
document.documentElement.appendChild(script);
script.remove();