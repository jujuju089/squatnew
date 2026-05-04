import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Squat Analyzer", layout="wide")

st.title("Squat Pose Analyzer")
st.write("Diese App nutzt MediaPipe JS, um Squats ohne OpenCV/libGL zu analysieren.")

# Das HTML/JavaScript Paket für die Browser-Verarbeitung
html_code = """
<div style="position: relative;">
    <video id="input_video" style="display:none;"></video>
    <canvas id="output_canvas" style="width: 100%; max-width: 800px; border-radius: 10px;"></canvas>
    <div id="status" style="position: absolute; top: 20px; left: 20px; color: white; background: rgba(0,0,0,0.5); padding: 10px; font-family: sans-serif;">
        Winkel: <span id="angle_val">0</span>°<br>
        Status: <span id="squat_status">-</span>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/@mediapipe/pose"></script>
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils"></script>
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils"></script>

<script>
const videoElement = document.getElementById('input_video');
const canvasElement = document.getElementById('output_canvas');
const canvasCtx = canvasElement.getContext('2d');
const angleDisplay = document.getElementById('angle_val');
const statusDisplay = document.getElementById('squat_status');

function findAngle(p1, p2, p3) {
    let radians = Math.atan2(p3.y - p2.y, p3.x - p2.x) - Math.atan2(p1.y - p2.y, p1.x - p2.x);
    let angle = Math.abs(radians * 180.0 / Math.PI);
    if (angle > 180.0) angle = 360 - angle;
    return angle;
}

function onResults(results) {
    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);

    if (results.poseLandmarks) {
        drawConnectors(canvasCtx, results.poseLandmarks, POSE_CONNECTIONS, {color: '#00FF00', lineWidth: 4});
        drawLandmarks(canvasCtx, results.poseLandmarks, {color: '#FF0000', lineWidth: 2});

        // Landmarker: 24=Hüfte, 26=Knie, 28=Ankle (Rechte Seite als Beispiel)
        const hip = results.poseLandmarks[24];
        const knee = results.poseLandmarks[26];
        const ankle = results.poseLandmarks[28];

        const angle = findAngle(hip, knee, ankle);
        angleDisplay.innerText = Math.round(angle);

        if (angle < 100) {
            statusDisplay.innerText = "TIEFER SQUAT";
            statusDisplay.style.color = "#00FF00";
        } else if (angle > 160) {
            statusDisplay.innerText = "STEHEND";
            statusDisplay.style.color = "white";
        } else {
            statusDisplay.innerText = "GEHE TIEFER...";
            statusDisplay.style.color = "yellow";
        }
    }
    canvasCtx.restore();
}

const pose = new Pose({locateFile: (file) => {
    return `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`;
}});

pose.setOptions({ modelComplexity: 1, smoothLandmarks: true, minDetectionConfidence: 0.5, minTrackingConfidence: 0.5 });
pose.onResults(onResults);

const camera = new Camera(videoElement, {
    onFrame: async () => {
        await pose.send({image: videoElement});
    },
    width: 1280,
    height: 720
});
camera.start();
</script>
"""

# Komponente in Streamlit einbetten
components.html(html_code, height=600)

st.info("Hinweis: Beim ersten Start bittet der Browser um Kamerazugriff. Die Verarbeitung erfolgt lokal.")
