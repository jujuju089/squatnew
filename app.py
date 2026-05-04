import streamlit as st
import streamlit.components.v1 as components
import base64

st.set_page_config(page_title="Ultimate Squat Analyzer", layout="wide")

st.title("Squat Analyzer Pro")
st.subheader("Web-Native (No OpenCV / No libGL)")

# Auswahl des Modus
mode = st.radio("Modus wählen:", ["Live Kamera", "Video Hochladen"], horizontal=True)

video_data_url = ""
if mode == "Video Hochladen":
    uploaded_file = st.file_uploader("Video auswählen", type=["mp4", "mov", "avi"])
    if uploaded_file:
        video_bytes = uploaded_file.read()
        video_base64 = base64.b64encode(video_bytes).decode()
        video_data_url = f"data:video/mp4;base64,{video_base64}"
    else:
        st.info("Bitte lade ein Video hoch.")
        st.stop()

# Das kombinierte HTML/JS Snippet
html_code = f"""
<div id="container" style="position: relative; font-family: sans-serif;">
    <div id="ui" style="background: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px; display: flex; gap: 20px; align-items: center;">
        <div><strong>Winkel:</strong> <span id="angle_val">0</span>°</div>
        <div><strong>Status:</strong> <span id="squat_status">-</span></div>
        {"<button id='switch_cam' style='padding: 8px; cursor: pointer;'>Kamera wechseln</button>" if mode == "Live Kamera" else ""}
    </div>

    <div style="position: relative; display: inline-block;">
        <video id="input_video" {"controls" if mode == "Video Hochladen" else "autoplay playsinline"} 
               src="{video_data_url}" style="max-width: 100%; border-radius: 10px; background: #000;"></video>
        <canvas id="output_canvas" style="position: absolute; top: 0; left: 0; pointer-events: none;"></canvas>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/@mediapipe/pose"></script>
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils"></script>
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils"></script>

<script>
const videoElement = document.getElementById('input_video');
const canvasElement = document.getElementById('output_canvas');
const canvasCtx = canvasElement.getContext('2d');
const angleDisplay = document.getElementById('angle_val');
const statusDisplay = document.getElementById('squat_status');

let currentFacingMode = "user"; // Standard: Frontkamera

function findAngle(p1, p2, p3) {{
    let radians = Math.atan2(p3.y - p2.y, p3.x - p2.x) - Math.atan2(p1.y - p2.y, p1.x - p2.x);
    let angle = Math.abs(radians * 180.0 / Math.PI);
    if (angle > 180.0) angle = 360 - angle;
    return angle;
}}

const pose = new Pose({{locateFile: (file) => {{
    return `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${{file}}`;
}}}});

pose.setOptions({{ modelComplexity: 1, smoothLandmarks: true, minDetectionConfidence: 0.5, minTrackingConfidence: 0.5 }});

pose.onResults((results) => {{
    canvasElement.width = videoElement.clientWidth;
    canvasElement.height = videoElement.clientHeight;
    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    
    if (results.poseLandmarks) {{
        drawConnectors(canvasCtx, results.poseLandmarks, POSE_CONNECTIONS, {{color: '#00FF00', lineWidth: 3}});
        
        // Rechter Squat-Winkel (24, 26, 28)
        const hip = results.poseLandmarks[24];
        const knee = results.poseLandmarks[26];
        const ankle = results.poseLandmarks[28];

        if (hip && knee && ankle) {{
            const angle = findAngle(hip, knee, ankle);
            angleDisplay.innerText = Math.round(angle);
            if (angle < 100) {{ statusDisplay.innerText = "TIEF"; statusDisplay.style.color = "green"; }}
            else if (angle > 160) {{ statusDisplay.innerText = "HOCH"; statusDisplay.style.color = "blue"; }}
            else {{ statusDisplay.innerText = "SQUAT..."; statusDisplay.style.color = "orange"; }}
        }}
    }}
    canvasCtx.restore();
}});

// --- LOGIK FÜR LIVE KAMERA ---
if ("{mode}" === "Live Kamera") {{
    let camera = null;
    
    async function startCamera(mode) {{
        if (camera) await camera.stop();
        camera = new Camera(videoElement, {{
            onFrame: async () => {{ await pose.send({{image: videoElement}}); }},
            width: 1280, height: 720,
            facingMode: mode 
        }});
        camera.start();
    }}

    startCamera(currentFacingMode);

    const btn = document.getElementById('switch_cam');
    if(btn) btn.onclick = () => {{
        currentFacingMode = (currentFacingMode === "user") ? "environment" : "user";
        startCamera(currentFacingMode);
    }};
}} 
// --- LOGIK FÜR VIDEO UPLOAD ---
else {{
    async function processFrame() {{
        if (!videoElement.paused && !videoElement.ended) {{
            await pose.send({{image: videoElement}});
        }}
        requestAnimationFrame(processFrame);
    }}
    videoElement.addEventListener('play', processFrame);
}}
</script>
"""

components.html(html_code, height=800)

st.markdown("""
### Anleitung:
1. **Live Kamera:** Erlaubt den Zugriff auf deine Webcam. Nutze den Button zum Wechseln auf die Rückkamera.
2. **Video Upload:** Lade eine Datei hoch und drücke Play im Video-Player.
3. **Winkel:** Die App berechnet den Winkel am Knie. Ziel ist < 100°.
""")
