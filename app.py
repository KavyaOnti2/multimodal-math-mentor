from rag.retriever import retrieve_context
from agents.solver_agent import solver_agent
from agents.router_agent import router_agent
from agents.parser_agent import parser_agent
from utils.ocr_cleaner import clean_ocr_math
from utils.confidence_fusion import compute_final_confidence
from utils.memory_learning import get_failure_patterns
from agents.verifier_agent import verifier_agent
from utils.memory_runtime import find_similar_past_problems, memory_success_boost
from agents.explainer_agent import explainer_agent
import streamlit as st
import os
import json
from datetime import datetime
MEMORY_FILE = "data/system_memory.json"

from tools.ocr import extract_text_from_image
from tools.asr import transcribe_audio
from tools.confidence import is_low_confidence
from config import OCR_CONF_THRESHOLD, ASR_CONF_THRESHOLD

# =====================================================
# 🧠 SESSION STATE INIT
# =====================================================
def init_state(key, default):
    if key not in st.session_state:
        st.session_state[key] = default
init_state("system_memory", [])

# load persistent memory
if os.path.exists(MEMORY_FILE):
    try:
        with open(MEMORY_FILE, "r") as f:
            st.session_state.system_memory = json.load(f)
    except Exception:
        st.session_state.system_memory = []
# =====================================================
# 💾 MEMORY SAVE HELPER
# =====================================================
def save_system_memory():
    os.makedirs("data", exist_ok=True)
    with open(MEMORY_FILE, "w") as f:
        json.dump(st.session_state.system_memory, f, indent=2)
# =====================================================
# 🧠 MEMORY ENTRY BUILDER (SELF-LEARNING CORE)
# =====================================================
def build_memory_entry(
    input_mode,
    original_input,
    parsed_output,
    retrieved_chunks,
    solver_output,
    verifier_output,
):
    return {
        "timestamp": datetime.now().isoformat(),
        "input_mode": input_mode,
        "original_input": original_input,

        # Parser data
        "parsed_question": parsed_output.get("problem_text") if parsed_output else "",
        "topic": parsed_output.get("topic") if parsed_output else "",

        # RAG data
        "retrieved_context": [c[0] for c in retrieved_chunks] if retrieved_chunks else [],

        # Solver data
        "final_answer": solver_output.get("final_answer") if solver_output else "",
        "solver_status": solver_output.get("status") if solver_output else "",

        #  Verifier data 
        "verifier_outcome": verifier_output.get("verdict") if verifier_output else "",
        "verifier_confidence": verifier_output.get("confidence") if verifier_output else 0.0,
        "verifier_reason": verifier_output.get("reason") if verifier_output else "",

        # Feedback placeholder 
        "feedback": None,
    }
# =====================================================
#  FULL RESET AFTER FEEDBACK
# =====================================================
def full_reset():

    keys_to_clear = [
        "hitl_editor",
        "clarified_text",
        "clarification_mode",
        "transcription",
        "audio_saved",
        "confidence",
        "feedback_given",
        "feedback_type",
        "feedback_comment",
    ]

    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

    #  Force new input widget
    st.session_state.widget_version += 1

    st.rerun()
init_state("audio_saved", False)
init_state("transcription", "")
init_state("confidence", 0.0)
init_state("audio_path", None)

# clarification
init_state("clarification_mode", False)
init_state("clarified_text", "")
init_state("clarify_input", "")
init_state("hitl_editor", "")

# memory
init_state("chat_history", [])

# feedback
init_state("feedback_given", False)
init_state("feedback_type", None)
init_state("feedback_log", [])


init_state("last_input_mode", None)
init_state("widget_version", 0)


# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Multimodal Math Mentor",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Multimodal Math Mentor")
st.caption("AI system for solving JEE-style math problems")

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.header("Input Mode")
input_mode = st.sidebar.radio(
    "Choose input type:",
    ["Text", "Image", "Audio"]
)

# =====================================================
#  RESET WHEN INPUT MODE CHANGES 
# =====================================================
if st.session_state.last_input_mode != input_mode:
    # clear editor + pipeline state
    st.session_state.hitl_editor = ""
    st.session_state.clarified_text = ""
    st.session_state.clarification_mode = False
    st.session_state.clarify_input = ""

    # clear audio/image leftovers
    st.session_state.transcription = ""
    st.session_state.audio_saved = False
    st.session_state.confidence = 0.0

    # reset feedback
    st.session_state.feedback_given = False
    st.session_state.feedback_type = None

    # update tracker
    st.session_state.last_input_mode = input_mode

extracted_text = ""
confidence_score = st.session_state.confidence
hitl_required = False

# =====================================================
# TEXT INPUT
# =====================================================
if input_mode == "Text":
    user_text = st.text_area(
        "Enter math problem:",
        key=f"input_box_{st.session_state.widget_version}"
    )

    if st.button("Process Text"):
        extracted_text = user_text
        st.session_state.confidence = 1.0

        #  PUSH INTO HITL EDITOR IMMEDIATELY
        st.session_state.hitl_editor = user_text.strip()

        # reset feedback
        st.session_state.feedback_given = False
        st.session_state.feedback_type = None

        st.rerun()

        # reset feedback
        st.session_state.feedback_given = False
        st.session_state.feedback_type = None

# =====================================================
# IMAGE INPUT
# =====================================================
elif input_mode == "Image":
    uploaded_image = st.file_uploader(
        "Upload math problem image",
        type=["png", "jpg", "jpeg"]
    )

    if uploaded_image is not None:
        if st.button("Run OCR"):
            save_path = os.path.join("data/uploads", uploaded_image.name)
            os.makedirs("data/uploads", exist_ok=True)

            with open(save_path, "wb") as f:
                f.write(uploaded_image.getbuffer())

            with st.spinner("Running OCR..."):
                extracted_text, confidence_score = extract_text_from_image(save_path)
                extracted_text = clean_ocr_math(extracted_text)

            st.session_state.hitl_editor = extracted_text.strip()
            st.session_state.confidence = confidence_score


            if is_low_confidence(confidence_score, OCR_CONF_THRESHOLD):
                hitl_required = True

            # reset feedback
            st.session_state.feedback_given = False
            st.session_state.feedback_type = None
            st.rerun()

# =====================================================
# AUDIO INPUT
# =====================================================
elif input_mode == "Audio":
    st.subheader("🎤 Audio Input")

    from streamlit_mic_recorder import mic_recorder

    uploaded_audio = st.file_uploader(
        "Upload audio question",
        type=["wav", "mp3", "m4a"]
    )

    st.write("OR record from microphone:")

    audio_bytes = mic_recorder(
        start_prompt="Start Recording",
        stop_prompt="Stop Recording",
        key="recorder"
    )

    if audio_bytes:
        os.makedirs("data/uploads", exist_ok=True)

        st.session_state.audio_path = "data/uploads/recorded_audio.wav"
        with open(st.session_state.audio_path, "wb") as f:
            f.write(audio_bytes["bytes"])

        st.session_state.audio_saved = True
        st.session_state.transcription = ""
        st.session_state.confidence = 0.0

    elif uploaded_audio:
        os.makedirs("data/uploads", exist_ok=True)

        st.session_state.audio_path = os.path.join(
            "data/uploads",
            uploaded_audio.name
        )

        with open(st.session_state.audio_path, "wb") as f:
            f.write(uploaded_audio.getbuffer())

        st.session_state.audio_saved = True
        st.session_state.transcription = ""
        st.session_state.confidence = 0.0

    if st.session_state.audio_saved:
        st.success("Recording saved!")

    if st.session_state.audio_path and st.button("Run Transcription"):
        with st.spinner("Transcribing audio..."):
            text, conf = transcribe_audio(st.session_state.audio_path)

        st.session_state.transcription = text
        st.session_state.confidence = conf
        st.session_state.audio_saved = False

         #  CRITICAL FIX — push to HITL editor
        st.session_state.hitl_editor = text.strip()

        # reset feedback
        st.session_state.feedback_given = False
        st.session_state.feedback_type = None

        st.rerun()
        if is_low_confidence(conf, ASR_CONF_THRESHOLD):
            hitl_required = True

        #  FIXED RESET POSITION
        st.session_state.feedback_given = False
        st.session_state.feedback_type = None

    extracted_text = st.session_state.transcription
    confidence_score = st.session_state.confidence

# =====================================================
# PIPELINE
# =====================================================

effective_text = (
    st.session_state.clarified_text.strip()
    if st.session_state.clarified_text
    else st.session_state.hitl_editor.strip()
)

parsed_output = None
route_output = None
solver_output = None
verifier_output = None
explainer_output = None
similar_memories = []
success_count = 0

# -----------------------------------------------------
# 1️ Parser
# -----------------------------------------------------
if effective_text:
    parsed_output = parser_agent(effective_text)

# -----------------------------------------------------
# 2️ Router
# -----------------------------------------------------
if parsed_output:
    route_output = router_agent(parsed_output)

    if route_output.get("route") == "clarify":
        st.session_state.clarification_mode = True

# -----------------------------------------------------
# 3️ Solve Route
# -----------------------------------------------------
failure_stats = get_failure_patterns(st.session_state.system_memory)

if route_output and route_output.get("route") == "solve":

    #  Memory-aware OCR caution
    if failure_stats.get("ocr_noise", 0) > 5 and confidence_score < 0.7:
        st.warning("⚠️ System detected frequent OCR issues. Review input carefully.")

    # 3️ Solver
    solver_output = solver_agent(parsed_output)

    if solver_output:

        # 4️ Verifier (Independent Agent)
        verifier_output = verifier_agent(parsed_output, solver_output)

        #  Verifier-triggered HITL
        if verifier_output and verifier_output["verdict"] == "fail":
            st.warning(
                f"⚠️ Verifier confidence low ({verifier_output['confidence']:.2f}). Please review."
            )
            st.session_state.clarification_mode = True
        #Explainer Agent
        explainer_output = None

        if solver_output.get("status") == "success":
            explainer_output = explainer_agent(parsed_output, solver_output)


        # 5️ Memory Runtime Influence (ONLY when solving)
        similar_memories = find_similar_past_problems(
            st.session_state.system_memory,
            effective_text,
        )

        success_count = memory_success_boost(similar_memories)

        if success_count > 0:
            st.success(
                f"🔁 Reused reasoning from {success_count} similar past problem(s)."
            )

# -----------------------------------------------------
# 6️ Adaptive Confidence Fusion
# -----------------------------------------------------
final_confidence = compute_final_confidence(
    confidence_score,
    parsed_output,
    solver_output,
)

# Fuse verifier confidence
if verifier_output:
    final_confidence = (final_confidence + verifier_output["confidence"]) / 2

# Boost from memory success
if success_count > 0:
    final_confidence = min(final_confidence + 0.05 * success_count, 1.0)


# =====================================================
# UI PANELS
# =====================================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("🔍 Extracted Text")

    #  SINGLE SOURCE OF TRUTH FOR EDITOR
    if extracted_text and not st.session_state.hitl_editor:
        st.session_state.hitl_editor = extracted_text

    if st.session_state.hitl_editor:
        if hitl_required:
            st.warning("⚠️ Low confidence detected — please verify")

        st.text_area(
            label="Edit if needed (HITL):",
            key="hitl_editor",
            height=150,
        )
    else:
        st.info("Will appear after processing")

with col2:
    st.subheader("📊 Confidence Score")
    display_conf = final_confidence if effective_text else 0.0
    st.metric("Confidence", f"{confidence_score:.2f}")

# =====================================================
# AGENT TRACE
# =====================================================
st.subheader("🧩 Agent Trace")

if parsed_output:
    st.json(parsed_output)

if route_output:
    st.subheader("🧭 Router Decision")
    st.json(route_output)
# =====================================================
# 🔬 SYSTEM INTERNALS 
# =====================================================

with st.expander("🔬 System Diagnostics (AI Internals)"):

    st.write("**Detected Topic:**", parsed_output.get("topic") if parsed_output else "N/A")

    st.write("**Solver Status:**",
             solver_output.get("status") if solver_output else "Not executed")

    st.write("**Final Confidence:**", round(final_confidence, 3))

    if verifier_output:
        st.write("**Verifier Confidence:**", verifier_output.get("confidence"))

    st.write("**Memory Matches:**", success_count)

    if route_output:
        st.write("**Routing Decision:**", route_output.get("route"))


# =====================================================
# 📚 RAG 
# =====================================================
st.subheader("📚 Retrieved Context")

def get_score_label(score: float) -> str:
    if score >= 0.75:
        return "🟢 High relevance"
    elif score >= 0.5:
        return "🟡 Medium relevance"
    else:
        return "🔴 Low relevance"

retrieved_chunks = []

if (
    route_output
    and route_output.get("route") == "solve"
    and effective_text
):
    with st.spinner("Retrieving knowledge..."):
        retrieved_chunks = retrieve_context(effective_text)

    #  memory-aware reranking boost (SAFE VERSION)
    if retrieved_chunks and st.session_state.system_memory:
        past_success = sum(
            1
            for m in st.session_state.system_memory
            if m.get("verifier_outcome") == "success"
        )

        if past_success > 5:
            retrieved_chunks = [
                (chunk, min(score + 0.05, 1.0))
                for chunk, score in retrieved_chunks
            ]
    if retrieved_chunks:
        st.success(f"Top {len(retrieved_chunks)} relevant knowledge chunks")

        for i, (chunk, score) in enumerate(retrieved_chunks, 1):
            label = get_score_label(score)

            st.markdown(
                f"""
                <div style="
                    padding:14px;
                    border-radius:14px;
                    background-color:#1e293b;
                    margin-bottom:14px;
                    border-left:6px solid #22c55e;
                    color:white;
                    box-shadow: 0 4px 14px rgba(0,0,0,0.25);
                ">
                <div style="display:flex; justify-content:space-between;">
                    <b style="color:#22c55e;">Chunk {i}</b>
                    <span style="color:#94a3b8;">
                        score: {score:.3f}
                    </span>
                </div>

                <div style="margin-top:6px; font-size:13px; color:#facc15;">
                    {label}
                </div>

                <hr style="border-color:#334155;">

                <div style="font-size:15px; line-height:1.5;">
                    {chunk}
                </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.warning("⚠️ No relevant context found in knowledge base.")
else:
    st.info("📌 Context will appear after problem is ready to solve.")

# =====================================================
#  FINAL ANSWER
# =====================================================

st.subheader("✅ Final Answer")

if solver_output is not None:

    # ----------------------------
    # 1️ Solver Output
    # ----------------------------
    st.json(solver_output)

    # ----------------------------
    # 2️ Verifier Output
    # ----------------------------
    if verifier_output:
        st.subheader("🔎 Verifier Output")
        st.json(verifier_output)

    # ----------------------------
    # 3️ Explainer Output
    # ----------------------------
    if explainer_output:
        st.subheader("📘 Tutor Explanation")
        st.write(explainer_output["explanation"])

        if explainer_output.get("steps"):
            st.subheader("🧩 Step-by-Step Solution")
            for step in explainer_output["steps"]:
                st.markdown(f"- {step}")

    # =========================================
    # 🧠 STORE SYSTEM MEMORY
    # =========================================
    memory_entry = build_memory_entry(
        input_mode=input_mode,
        original_input=effective_text,
        parsed_output=parsed_output,
        retrieved_chunks=retrieved_chunks,
        solver_output=solver_output,
        verifier_output=verifier_output,
    )

    if (
        not st.session_state.system_memory
        or st.session_state.system_memory[-1]["original_input"]
        != memory_entry["original_input"]
    ):
        st.session_state.system_memory.append(memory_entry)
        save_system_memory()

    # =========================================
    # 💬 CHAT HISTORY
    # =========================================
    safe_answer = solver_output.get("final_answer", "")

    if safe_answer:
        if (
            not st.session_state.chat_history
            or st.session_state.chat_history[-1]["question"] != effective_text
        ):
            st.session_state.chat_history.append(
                {
                    "question": effective_text,
                    "answer": safe_answer,
                }
            )

else:
    st.info("Solver will run after routing")

# =====================================================
# 📝 FEEDBACK (AUTO RESET VERSION)
# =====================================================
st.subheader("📝 Feedback")

col_a, col_b = st.columns(2)

with col_a:
    correct_clicked = st.button("✅ Correct")

with col_b:
    incorrect_clicked = st.button("❌ Incorrect")

# ----------------------------
# ✅ CORRECT
# ----------------------------
if correct_clicked:
    if st.session_state.system_memory:
        st.session_state.system_memory[-1]["feedback"] = {
            "label": "correct",
            "comment": "",
        }
        save_system_memory()

    full_reset()


# ----------------------------
# ❌ INCORRECT
# ----------------------------
if incorrect_clicked:
    st.session_state.feedback_type = "incorrect"


if st.session_state.get("feedback_type") == "incorrect":
    comment = st.text_area(
        "Please tell us what was wrong:",
        key="feedback_comment",
    )

    if st.button("Submit Feedback") and comment.strip():

        if st.session_state.system_memory:
            st.session_state.system_memory[-1]["feedback"] = {
                "label": "incorrect",
                "comment": comment,
            }
            save_system_memory()

        full_reset()

# =====================================================
# 🧠 MEMORY
# =====================================================
st.subheader("🧠 Conversation History")

if st.session_state.chat_history:
    for i, chat in enumerate(reversed(st.session_state.chat_history), 1):
        st.markdown(
            f"""
            <div style="
                padding:12px;
                border-radius:12px;
                background-color:#0f172a;
                margin-bottom:10px;
                border-left:5px solid #38bdf8;
                color:white;
            ">
            <b style="color:#38bdf8;">Q{i}:</b> {chat['question']}<br><br>
            <b style="color:#22c55e;">A:</b> {chat['answer']}
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.info("No conversation history yet.")

