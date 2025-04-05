export class VideoProcessor {
  constructor(constraints, originalGetUserMedia) {
    this.constraints = constraints;
    this.originalGetUserMedia = originalGetUserMedia;
  }

  async process() {
    console.log("VideoProcessor: Starting processing");
    const rawStream = await this.originalGetUserMedia.call(navigator.mediaDevices, this.constraints);
    console.log("VideoProcessor: Received raw stream");

    // Create video element to play the raw stream
    const video = document.createElement("video");
    video.srcObject = rawStream;
    video.muted = true;
    video.playsInline = true;
    await video.play();
    console.log("VideoProcessor: Video playing", video.videoWidth, video.videoHeight);

    // Create canvas to capture frames
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");

    // Capture a processed stream from the canvas
    const processedStream = canvas.captureStream(15); // e.g., 15 fps
    const finalStream = new MediaStream();

    const render = async () => {
      // Draw the current video frame onto the canvas
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      console.log("VideoProcessor: Drew video frame to canvas");

      try {
        // Convert canvas to blob and send it to the Python server
        const blob = await this.sendFrameToServer(canvas);
        console.log("VideoProcessor: Received blurred frame from server");

        // Create an image from the processed blob
        const img = new Image();
        img.onload = () => {
          // Draw the processed (blurred) frame onto the canvas
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
          console.log("VideoProcessor: Rendered blurred image on canvas");
          // Continue processing the next frame
          requestAnimationFrame(render);
        };
        img.src = URL.createObjectURL(blob);
      } catch (error) {
        console.error("VideoProcessor: Error processing frame:", error);
        requestAnimationFrame(render);
      }
    };

    video.addEventListener("play", () => {
      requestAnimationFrame(render);
    });

    // Pipe the processed video track to the final stream
    processedStream.getVideoTracks().forEach((track) => finalStream.addTrack(track));
    // Include original audio tracks if requested
    if (this.constraints.audio) {
      rawStream.getAudioTracks().forEach((track) => finalStream.addTrack(track));
    }

    return finalStream;
  }

  async sendFrameToServer(canvas) {
    return new Promise((resolve, reject) => {
      canvas.toBlob(async (blob) => {
        if (!blob) {
          return reject("Canvas blob conversion failed");
        }
        const formData = new FormData();
        formData.append("file", blob, "frame.jpg");

        try {
          const response = await fetch("http://127.0.0.1:8000/blur", {
            method: "POST",
            body: formData,
          });
          if (!response.ok) {
            return reject("Server responded with status " + response.status);
          }
          const resultBlob = await response.blob();
          resolve(resultBlob);
        } catch (error) {
          reject(error);
        }
      }, "image/jpeg");
    });
  }
}
