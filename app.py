import streamlit as st
import streamlit.components.v1 as components
import base64

st.set_page_config(page_title="Squat Master Pro", layout="wide")

st.title("🏋️‍♂️ Squat Analyzer & Tracker")
st.write("Analyse über MediaPipe – Browser-nativ (Kein OpenCV / libGL benötigt).")

mode = st.radio("Modus wählen:", ["Kamera Live", "Video Upload"], horizontal=True)

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

# Das HTML/JS Snippet mit dem "Fertig"-Button
html_code = f"""
<div id="app-container" style="font-family: sans-serif; max-width: 900px; margin: auto;">
    
    <!-- DASHBOARD -->
    <div id="dashboard" style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; background: #1e1e1e; color: white; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
        <div style="text-align: center;">
            <span style="font-size: 0.8em; opacity: 0.7;">WINKEL</span><br>
            <strong style="font-size: 1.5em; color: #00d4ff;"><span id="angle_val">0</span>°</strong>
        </div>
        <div style="text-align: center;">
            <span style="font-size: 0.8em; opacity: 0.7;">REPS</span><br>
            <strong style="font-size: 1.5em; color: #44ff44;"><span id="rep_count">0</span></strong>
        </div>
        <div style="text-align: center;">
            <span style="font-size: 0.8em; opacity: 0.7;">STATUS</span><br>
            <strong id="squat_status" style="font-size: 1.1em; color: #ffcc00;">BEREIT</strong>
        </div>
    </div>

    <!-- VIDEO/CANVAS AREA -->
    <div style="position: relative; background: #000; border-radius: 10px; overflow: hidden; line-height: 0;">
        <video id="input_video" {"controls" if mode == "Video Upload" else "autoplay playsinline"} 
               src="{video_data_url}" style="width: 100%; height: auto;"></video>
        <canvas id="output_canvas" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;"></canvas>
    </div>

    <!-- CONTROLS -->
    <div style="margin-top: 15px; display: flex; gap: 10px;">
        {"<button id='switch_cam' style='flex: 1; padding: 12px; background: #444; color: white; border: none; border-radius: 5px; cursor: pointer;'>Kamera wechseln</button>" if mode == "Kamera Live" else ""}
        <button id="finish_btn" style="flex: 1; padding: 12px; background: #ff4b4b; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">Workout beenden & Auswerten</button>
    </div>

    <!-- SUMMARY OVERLAY (HIDDEN BY DEFAULT) -->
    <div id="summary_overlay" style="display:none; margin-top: 20px; padding: 25px; background: #f0f2f6; border-radius: 10px; border-left: 8px solid #ff4b4b; animation: fadeIn 0.5s;">
        <h2 style="margin-top: 0;">📊 Dein Ergebnis</h2>
        <div id="summary_content" style="font-size: 1.3em; line-height: 1.6;"></div>
        <button onclick="window.location.reload()" style="margin-top: 15px; padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;">Neues Training</button>
    </div>
</div>

<style>
@keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
</style>

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
const finishBtn = document.getElementById('finish_btn');
const summaryOverlay = document.getElementById('summary_overlay');
const summaryContent = document.getElementById('summary_content');

let count = 0;
let stage = "up";
let deepReps = 0;
let isActive = true;

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
    if (!isActive) return;

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

            // Counter Logik
            if (angle > 160) {{
                if (stage === "down") {{
                    count++;
                    repDisplay.innerText = count;
                }}
                stage = "up";
                statusDisplay.innerText = "RUNTER GEHEN";
                statusDisplay.style.color = "#00d4ff";
            }}
            if (angle < 100) {{
                if (stage === "up") {{
                    deepReps++; 
                }}
                stage = "down";
                statusDisplay.innerText = "TIEFE HALTEN";
                statusDisplay.style.color = "#44ff44";
            }}
        }}
    }}
    canvasCtx.restore();
}});

function finishWorkout() {{
    isActive = false;
    summaryOverlay.style.display = "block";
    const quality = count > 0 ? Math.round((deepReps / count) * 100) : 0;
    
    let feedback = quality > 80 ? "🔥 Exzellente Form!" : (quality > 50 ? "👍 Gute Arbeit, versuch noch tiefer zu gehen." : "⚠️ Achte mehr auf die Tiefe deiner Squats.");
    
    summaryContent.innerHTML = `
        Wiederholungen: <strong>${{count}}</strong><br>
        Gute Form (Tiefe): <strong>${{quality}}%</strong><br><br>
        <em>${{feedback}}</em>
    `;
    
    // Video/Kamera stoppen
    if (videoElement.srcObject) {{
        videoElement.srcObject.getTracks().forEach(track => track.stop());
    }}
    videoElement.pause();
    finishBtn.style.display = "none";
}}

finishBtn.onclick = finishWorkout;
videoElement.onended = finishWorkout;

// --- KAMERA / VIDEO INIT ---
if ("{mode}" === "Kamera Live") {{
    let currentFacingMode = "user";
    let camera = null;
    
    async function startCamera(fm) {{
        if (camera) await camera.stop();
        camera = new Camera(videoElement, {{
            onFrame: async () => {{ if(isActive) await pose.send({{image: videoElement}}); }},
            width: 1280, height: 720, facingMode: fm 
        }});
        camera.start();
    }}
    startCamera(currentFacingMode);
    
    if (document.getElementById('switch_cam')) {{
        document.getElementById('switch_cam').onclick = () => {{
            currentFacingMode = (currentFacingMode === "user") ? "environment" : "user";
            startCamera(currentFacingMode);
        }};
    }}
}} else {{
    async function processFrame() {{
        if (isActive && !videoElement.paused && !videoElement.ended) {{
            await pose.send({{image: videoElement}});
        }}
        requestAnimationFrame(processFrame);
    }}
    videoElement.addEventListener('play', processFrame);
}}
</script>
"""

components.html(html_code, height=1000)
