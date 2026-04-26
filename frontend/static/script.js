// This function runs when button is clicked
function triggerAlert() {
    // Change text on screen
    document.getElementById("status").innerText = "⚠️ Risk detected";

    // Play alarm sound without external website
    playAlarm();
}

// This function creates a simple beep sound
function playAlarm() {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.type = "sine";
    oscillator.frequency.setValueAtTime(900, audioContext.currentTime);

    gainNode.gain.setValueAtTime(0.2, audioContext.currentTime);

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    oscillator.start();
    oscillator.stop(audioContext.currentTime + 0.5);
}