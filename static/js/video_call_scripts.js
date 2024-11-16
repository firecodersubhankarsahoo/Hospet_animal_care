// JavaScript for handling video call functionality

// DOM elements
const startCallButton = document.getElementById('startCallButton');
const endCallButton = document.getElementById('endCallButton');
const callInstructions = document.getElementById('callInstructions');
const videoCallContainer = document.getElementById('videoCallContainer');
const localVideo = document.getElementById('localVideo');
const remoteVideo = document.getElementById('remoteVideo');
const vetSelect = document.getElementById('vet');

let localStream;
let remoteStream;
let rtcPeerConnection;

// Start video call button click event
startCallButton.addEventListener('click', async () => {
    try {
        // Get selected veterinarian
        const selectedVet = vetSelect.value;

        // Get local media stream (audio and video)
        localStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: true });
        localVideo.srcObject = localStream;

        // Show call instructions
        callInstructions.style.display = 'block';

        // Initialize WebRTC peer connection
        rtcPeerConnection = new RTCPeerConnection();

        // Add local stream to peer connection
        localStream.getTracks().forEach(track => rtcPeerConnection.addTrack(track, localStream));

        // Set up event handlers for the peer connection

        // ICE candidate handling
        rtcPeerConnection.addEventListener('icecandidate', event => {
            if (event.candidate) {
                // Send the candidate to the remote peer
            }
        });

        // Handle remote stream
        rtcPeerConnection.addEventListener('track', event => {
            remoteStream = event.streams[0];
            remoteVideo.srcObject = remoteStream;
        });

        // Create offer to start communication
        const offer = await rtcPeerConnection.createOffer();
        await rtcPeerConnection.setLocalDescription(offer);

        // Send the SDP offer to the other peer (could be done via a signaling server)

        // Show the video call interface
        videoCallContainer.style.display = 'block';
    } catch (error) {
        console.error('Error starting video call:', error);
        alert('Error starting video call. Please check your device permissions and try again.');
    }
});

// End call button click event
endCallButton.addEventListener('click', () => {
    // Close the peer connection and stop all streams
    if (rtcPeerConnection) {
        rtcPeerConnection.close();
    }
    if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
    }
    if (remoteStream) {
        remoteStream.getTracks().forEach(track => track.stop());
    }

    // Reset video elements and hide the video call interface
    localVideo.srcObject = null;
    remoteVideo.srcObject = null;
    videoCallContainer.style.display = 'none';
});
