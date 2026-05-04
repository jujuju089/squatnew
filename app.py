import streamlit as st
import streamlit.components.v1 as components
import base64

st.set_page_config(page_title="Squat Video Analyzer", layout="wide")

st.title("Squat Video Analyzer")
st.write("Lade ein Video hoch. Die Analyse erfolgt rein im Browser (ohne OpenCV/libGL).")

# 1. Datei-Uploader in Streamlit
uploaded_file = st.file_uploader("Wähle ein Video aus (mp4, mov, avi)", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    # Video in Base64 konvertieren, um es an das JavaScript-Snippet zu übergeben
    video_bytes = uploaded_file.read()
    video_base64 = base64.b64encode(video_bytes).decode()
    video_data_url = f"data:video/mp4;base64,{video_base64}"

    # 2. HTML/JS Teil für die Analyse
    html_code = f"""
    <div style="position: relative;">
        <video id="input_video" src="{video_data_url}" controls style="max-width: 100%; border-radius: 10px;"></video>
        <canvas id="output_canvas" style="position: absolute; top: 0; left: 0; pointer-events: none;"></canvas>
        
        <div id="ui-overlay" style="margin-top: 10px; font-family: sans-serif; background: #f0f2f6; padding: 15px; border-radius: 10px;">
            <strong>Winkel:</strong> <span id="angle_val">0</span>° | 
            <strong>Status:</strong> <span id="squat_status">-</span>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/@mediapipe/pose"></script>
    <script src="https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils"></script>

    <script>
    const videoElement = document.getElementById('input_video');
    const canvasElement = document.getElementById('output_canvas');
    const canvasCtx = canvasElement.getContext('2d');
    const angleDisplay = document.getElementById('angle_val');
    const statusDisplay = document.getElementById('squat_status');

    function findAngle(p1, p2, p3) {{
        let radians = Math.atan2(p3.y - p2.y, p3.x - p2.x) - Math.atan2(p1.y - p2.y, p1.x - p2.x);
        let angle = Math.abs(radians * 180.0 / Math.PI);
        if (angle > 180.0) angle = 360 - angle;
        return angle;
    }}

    const pose = new Pose({{locateFile: (file) => {{
        return `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${{file}}`;
    }}}});

    pose.setOptions({{
        modelComplexity: 1,
        smoothLandmarks: true,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5
    }});

    pose.onResults((results) => {{
        // Canvas an Videogröße anpassen
        canvasElement.width = videoElement.clientWidth;
        canvasElement.height = videoElement.clientHeight;

        canvasCtx.save();
        canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
        
        if (results.poseLandmarks) {{
            // Zeichne Verbindungen
            drawConnectors(canvasCtx, results.poseLandmarks, POSE_CONNECTIONS, {{color: '#00FF00', lineWidth: 2}});
            
            // Logik für rechten Squat (Punkte 24, 26, 28)
            const hip = results.poseLandmarks[24];
            const knee = results.poseLandmarks[26];
            const ankle = results.poseLandmarks[28];

            const angle = findAngle(hip, knee, ankle);
            angleDisplay.innerText = Math.round(angle);

            if (angle < 100) {{
                statusDisplay.innerText = "GUTE TIEFE";
                statusDisplay.style.color = "green";
            }} else if (angle > 160) {{
                statusDisplay.innerText = "AUFRECHT";
                statusDisplay.style.color = "black";
            }} else {{
                statusDisplay.innerText = "IN BEWEGUNG";
                statusDisplay.style.color = "orange";
            }}
        }}
        canvasCtx.restore();
    }});

    // Frame-Verarbeitung synchron zum Video-Playback
    async function processFrame() {{
        if (!videoElement.paused && !videoElement.ended) {{
            await pose.send({{image: videoElement}});
        }}
        requestAnimationFrame(processFrame);
    }}

    videoElement.addEventListener('play', () => {{
        processFrame();
    }});
    </script>
    """

    components.html(html_code, height=800)

else:
    st.info("Bitte lade ein Video hoch, um die Analyse zu starten.")

st.markdown("---")
st.caption("Die Analyse findet lokal in deinem Browser statt. Es werden keine Videodaten an einen Server gesendet.")
