import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Winkel-App (Selbsttrainiert)", layout="wide")

st.title("📐 Selbsttrainierte Winkel-KI")
st.write("Diese Version nutzt DEINE mathematische Logik (Winkelberechnung).")

html_code = """
<div id="ai-app" style="font-family: sans-serif; background: #1a1a1a; color: white; padding: 20px; border-radius: 20px; max-width: 900px; margin: auto;">
    
    <div style="background: #2d2d2d; padding: 20px; border-radius: 12px; border-bottom: 4px solid #ffaa00; margin-bottom: 20px; text-align: center;">
        <div id="angle-label" style="font-size: 2em; font-weight: bold; color: #ffaa00;">Winkel: 0°</div>
        <div id="status-text" style="font-size: 1em; color: #888;">Suche Gelenke...</div>
    </div>

    <div style="position: relative; border-radius: 15px; overflow: hidden; background: #000;">
        <video id="video" autoplay playsinline muted style="width: 100%; height: auto;"></video>
        <canvas id="canvas" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></canvas>
    </div>

    <div style="display: flex; gap: 10px; margin-top: 20px;">
        <button id="switch-btn" style="flex: 1; padding: 15px; background: #444; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">📷 Kamera wechseln</button>
        <button id="stop-btn" style="flex: 1; padding: 15px; background: #ff4b4b; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">⏹ Stoppen</button>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
<script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/pose-detection"></script>

<script>
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const angleLabel = document.getElementById('angle-label');
const statusText = document.getElementById('status-text');

let detector;
let currentFacingMode = 'environment'; // Startet mit Rückkamera für das Tab S7
let active = true;

// WINKEL-BERECHNUNG (Deine Logik von gestern)
function calculateAngle(a, b, c) {
    let radians = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x);
    let angle = Math.abs(radians * 180.0 / Math.PI);
    if (angle > 180.0) angle = 360 - angle;
    return angle;
}

async function startStream() {
    try {
        if(video.srcObject) { video.srcObject.getTracks().forEach(t => t.stop()); }
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: currentFacingMode }
        });
        video.srcObject = stream;
        return new Promise(resolve => { video.onloadedmetadata = () => { video.play(); resolve(); }; });
    } catch (err) { alert("Kamera-Fehler!"); }
}

async function init() {
    detector = await poseDetection.createDetector(
        poseDetection.SupportedModels.MoveNet,
        { modelType: poseDetection.movenet.modelType.SINGLEPOSE_LIGHTNING }
    );
    await startStream();
    detect();
}

async function detect() {
    if (!active) return;
    if (video.readyState >= 2) {
        const poses = await detector.estimatePoses(video);
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (poses.length > 0) {
            const kp = poses[0].keypoints;
            
            // Punkte für den Kniewinkel: Hüfte(12), Knie(14), Knöchel(16)
            const hip = kp[12], knee = kp[14], ankle = kp[16];

            if (hip.score > 0.3 && knee.score > 0.3 && ankle.score > 0.3) {
                const angle = calculateAngle(hip, knee, ankle);
                angleLabel.innerText = "Winkel: " + Math.round(angle) + "°";
                
                if(angle < 100) statusText.innerText = "SQUAT!";
                else statusText.innerText = "Stehend";

                // Zeichne Linien für den Winkel
                ctx.strokeStyle = "#ffaa00";
                ctx.lineWidth = 5;
                ctx.beginPath();
                ctx.moveTo(hip.x, hip.y);
                ctx.lineTo(knee.x, knee.y);
                ctx.lineTo(ankle.x, ankle.y);
                ctx.stroke();
            }

            // Punkte zeichnen
            ctx.fillStyle = "white";
            kp.forEach(p => { if(p.score > 0.3) { ctx.beginPath(); ctx.arc(p.x, p.y, 5, 0, 2*Math.PI); ctx.fill(); } });
        }
    }
    requestAnimationFrame(detect);
}

document.getElementById('switch-btn').onclick = async () => {
    currentFacingMode = (currentFacingMode === 'user') ? 'environment' : 'user';
    await startStream();
};

document.getElementById('stop-btn').onclick = () => {
    active = false;
    if (video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
    video.pause();
};

init();
</script>
"""

components.html(html_code, height=900)
