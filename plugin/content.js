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
    // Check if the permission is already stored
    const storedState = await getStoredPermissionState(permission);
    if (storedState === "granted") {
      console.log(`${permission} is already granted. Skipping query.`);
      continue; // Skip querying if permission is already granted
    }

    // Query the permission state if not already granted
    const result = await getPermission(permission);
    console.log(result);

    // Save the permission state in storage
    savePermissionState(permission, result);
  }
}

// Query a single permission and return its state
async function getPermission(permission) {
  try {
    let result;
    if (permission === "top-level-storage-access") {
      result = await navigator.permissions.query({
        name: permission,
        requestedOrigin: window.location.origin,
      });
      result.onchange =  async (event) => {
        const storedState = await getStoredPermissionState(permission);
        if (storedState === "granted") {
          console.log(`${permission} is already granted. Skipping query.`);
          event.preventDefault();
          event.stopPropagation();
        }
      }
    } else {
      result = await navigator.permissions.query({ name: permission });
    }
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

// Load all saved permissions from storage (for debugging or initialization)
function loadPermissions() {
  browser.storage.local.get(permissions, (result) => {
    console.log("Loaded permissions from storage:", result);
  });
}

// Call this function to load permissions when needed
loadPermissions();

//Save the original getUserMedia function
const originalGetUserMedia = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);

//Declare the AudioContext globally
let audioContext;

// Function to initialize or resume the AudioContext
const initializeAudioContext = () => {
  if (!audioContext) {
    audioContext = new AudioContext();
    console.log("AudioContext created after user gesture hheeeeee");

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
}

document.addEventListener("click", initializeAudioContext);
document.addEventListener("keydown", initializeAudioContext);
document.addEventListener("touchstart", initializeAudioContext);
document.addEventListener("hover", initializeAudioContext);

const ensureAudioContextReady = async () => {
  if (!audioContext || audioContext.state === "suspended") {
    console.log("Waiting for AudioContext to be ready...");
    await initializeAudioContext();
  }
};

async function getMedia(constraints) {
  let stream = null;

  try {
    await ensureAudioContextReady();
    stream = await navigator.mediaDevices.getUserMedia(constraints);
    console.log("Website is requesting access to camera/microphone:", constraints);
    if (constraints.audio) {
         return originalGetUserMedia.call(navigator.mediaDevices, constraints)
           .then((stream) => {
            console.log("Original microphone stream intercepted");
           });
        }
  } catch (err) {
    console.error("Error accessing microphone:", error);
         throw error;
  }
}


//Override the getUserMedia function
navigator.mediaDevices.getUserMedia = async function (constraints) {
  console.log("Website is requesting access to camera/microphone:", constraints);

  if (constraints.audio) {
    return originalGetUserMedia.call(navigator.mediaDevices, constraints)
      .then((stream) => {
        console.log("Original microphone stream intercepted");

        // Add the AudioWorkletProcessor
        return audioContext.audioWorklet.addModule(URL.createObjectURL(new Blob([`
          class ScramblerProcessor extends AudioWorkletProcessor {
            process(inputs, outputs) {
              const input = inputs[0];
              const output = outputs[0];
              if (input && input[0]) {
                const inputChannel = input[0];
                const outputChannel = output[0];
                for (let i = 0; i < inputChannel.length; i++) {
                  const noise = (Math.random() * 0.2 - 0.1);
                  outputChannel[i] = inputChannel[i] + noise;
                }
              }
              return true;
            }
          }
          registerProcessor('scrambler', ScramblerProcessor);
        `], { type: 'application/javascript' }))).then(() => {
          const source = audioContext.createMediaStreamSource(stream);
          const scramblerNode = new AudioWorkletNode(audioContext, 'scrambler');
          const destination = audioContext.createMediaStreamDestination();

          // Connect the nodes
          source.connect(scramblerNode);
          console.log("Connected source to scramblerNode");
          scramblerNode.connect(destination);
          console.log("Connected scramblerNode to destination");

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
}

getMedia({ audio: true})