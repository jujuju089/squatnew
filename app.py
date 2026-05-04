import streamlit as st
import streamlit.components.v1 as components
import base64

st.set_page_config(page_title="Squat Master Pro", layout="wide")

st.title("🏋️‍♂️ Squat Analyzer & Counter")
st.write("Analyse über MediaPipe (Client-side) – Keine Serverlast, kein OpenCV.")

mode = st.radio("Modus:", ["Kamera Live", "Video Upload"], horizontal=True)

video_data_url = ""
if mode == "Video Upload":
    uploaded_file = st.file_uploader("Video hochladen", type=["mp4", "mov", "avi"])
    if uploaded_file:
        video_bytes = uploaded_file.read()
        video_base64 = base64.b64encode(video_bytes).decode()
        video_data_url = f"data:video/mp4;base64,{video_base64}"
    else:
        st.info("Bitte lade ein Video hoch.")
        st.stop()

# Das Herzstück: HTML5, CSS und die JS-Logik
html_code = f"""
<div id="app-container" style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333;">
    <div id="dashboard" style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; background: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <div style="text-align: center; border-right: 1px solid #ddd;">
            <span style="font-size: 0.8em; color: #666;">WINKEL</span><br>
            <strong style="font-size: 1.5em; color: #007bff;"><span id="angle_val">0</span>°</strong>
        </div>
        <div style="text-align: center; border-right: 1px solid #ddd;">
            <span style="font-size: 0.8em; color: #666;">REPS</span><br>
            <strong style="font-size: 1.5em; color: #28a745;"><span id="rep_count">0</span></strong>
        </div>
        <div style="text-align: center;">
            <span style="font-size: 0.8em; color: #666;">STATUS</span><br>
            <strong id="squat_status" style="font-size: 1.1em;">BEREIT</strong>
        </div>
    </div>

    <div style="position: relative; display: inline-block; width: 100%;">
        <video id="input_video" {"controls" if mode == "Video Upload" else "autoplay playsinline"} 
               src="{video_data_url}" style="width: 100%; border-radius: 10px; background: #000;"></video>
        <canvas id="output_canvas" style="position: absolute; top: 0; left: 0; pointer-events: none; width: 100%; height: 100%;"></canvas>
    </div>

    <div id="summary" style="margin-top: 20px; padding: 20px; background: #e9ecef; border-radius: 10px; display: none;">
        <h3>📊 Workout Zusammenfassung</h3>
        <p id="summary_text" style="font-size: 1.2em;"></p>
        <button onclick="window.location.reload()" style="padding: 10px 20px; cursor: pointer; background: #007bff; color: white; border: none; border-radius: 5px;">Neustart</button>
    </div>
    
    {"<button id='switch_cam' style='margin-top: 10px; padding: 10px; width: 100%; cursor: pointer; background: #6c757d; color: white; border: none; border-radius: 5px;'>Kamera wechseln (Front/Back)</button>" if mode == "Kamera Live" else ""}
</div>

<script src="https://cdn.jsdelivr.net/npm/@mediapipe/pose"></script>
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils"></script>
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils"></script>

<script>
const videoElement = document.getElementById('input_video');
const canvasElement = document.getElementById('output_canvas');
const canvasCtx = canvasElement.getContext('2d');
const angleDisplay = document.getElementById('angle_val');
const repDisplay = document.getElementById('rep_count');
const statusDisplay = document.getElementById('squat_status');
const summaryDiv = document.getElementById('summary');
const summaryText = document.getElementById('summary_text');

// Zähler Variablen
let count = 0;
let stage = "up"; // "up" oder "down"
let feedback = "";
let deepSquats = 0; // Qualitätstracker

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
    canvasElement.width = videoElement.videoWidth;
    canvasElement.height = videoElement.videoHeight;
    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    
    if (results.poseLandmarks) {{
        drawConnectors(canvasCtx, results.poseLandmarks, POSE_CONNECTIONS, {{color: '#00FF00', lineWidth: 4}});
        
        const hip = results.poseLandmarks[24];
        const knee = results.poseLandmarks[26];
        const ankle = results.poseLandmarks[28];

        if (hip && knee && ankle) {{
            const angle = findAngle(hip, knee, ankle);
            angleDisplay.innerText = Math.round(angle);

            // Squat Logik
            if (angle > 160) {{
                if (stage == "down") {{
                    count++;
                    repDisplay.innerText = count;
                }}
                stage = "up";
                statusDisplay.innerText = "RUNTER GEHEN";
                statusDisplay.style.color = "#007bff";
            }}
            if (angle < 100) {{
                if (stage == "up") {{
                    deepSquats++; // Zählt die "guten" Wiederholungen
                }}
                stage = "down";
                statusDisplay.innerText = "TIEFE HALTEN!";
                statusDisplay.style.color = "#28a745";
            }}
        }}
    }}
    canvasCtx.restore();
}});

// Beenden Funktion
function showSummary() {{
    summaryDiv.style.display = "block";
    const quality = count > 0 ? Math.round((deepSquats / count) * 100) : 0;
    summaryText.innerHTML = `Du hast <strong>${{count}}</strong> Wiederholungen geschafft.<br>` + 
                           `Qualität: <strong>${{quality}}%</strong> der Squats waren tief genug.`;
}}

videoElement.onended = showSummary;

// --- KAMERA / VIDEO KONTROLLE ---
if ("{mode}" === "Kamera Live") {{
    let currentFacingMode = "user";
    let camera = null;
    
    async function startCamera(fm) {{
        if (camera) await camera.stop();
        camera = new Camera(videoElement, {{
            onFrame: async () => {{ await pose.send({{image: videoElement}}); }},
            width: 1280, height: 720, facingMode: fm 
        }});
        camera.start();
    }}
    startCamera(currentFacingMode);
    
    const btn = document.getElementById('switch_cam');
    if(btn) btn.onclick = () => {{
        currentFacingMode = (currentFacingMode === "user") ? "environment" : "user";
        startCamera(currentFacingMode);
    }};
}} else {{
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

components.html(html_code, height=900)
