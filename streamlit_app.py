"""DecodeBot AI — Streamlit Web Application Demo.

A public-ready, interactive web interface for DecodeBot AI showcasing:
1. Chatbot Engine (100% deterministic rule-based conversational agent)
2. ML Playground (Supervised classification with scikit-learn)
3. Career Recommender (Content-based TF-IDF skill matching)
4. OCR Recognition (Image text extraction with OpenCV and Tesseract)
5. Architecture & About (System design and isolation principles)

This application reuses the existing DecodeBot engines without duplicating
business logic and conforms to the project's strict dependency boundaries.
"""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

import streamlit as st

from decodebot import __version__
from decodebot.core.config import load_config
from decodebot.core.dispatcher import dispatch
from decodebot.core.intents import Intent
from decodebot.core.rule_engine import classify_intent
from decodebot.core.session import SessionState
from decodebot.core.stats import get_session_duration
from decodebot.rules.help_about_version import get_reset_text
from streamlit_helpers import (
    classifier_label,
    combine_skills,
    exit_message,
    iris_preset_defaults,
    psm_label,
    reset_message,
    safe_upload_suffix,
    sample_image_path,
    welcome_message,
)

st.set_page_config(
    page_title="DecodeBot AI — Web Demo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a73e8;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #5f6368;
        margin-bottom: 1.2rem;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        font-size: 0.8rem;
        font-weight: 600;
        border-radius: 4px;
        margin-right: 0.4rem;
        margin-bottom: 0.4rem;
    }
    .badge-rule { background-color: #e8f0fe; color: #1a73e8; }
    .badge-ml { background-color: #fef7e0; color: #b06000; }
    .badge-rec { background-color: #f3e8fd; color: #7627bb; }
    .badge-ocr { background-color: #e6f4ea; color: #137333; }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        border-left: 4px solid #1a73e8;
        margin-bottom: 0.8rem;
    }
    .card-title { font-weight: 600; font-size: 0.95rem; color: #202124; }
    .card-value { font-size: 1.4rem; font-weight: 700; color: #1a73e8; }
    .stButton>button {
        border-radius: 6px;
        font-weight: 500;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _init_session() -> SessionState:
    """Initialize and persist the DecodeBot session in Streamlit session state."""
    if "session" not in st.session_state:
        config = load_config()
        session = SessionState()
        session.config = config
        session.start_time = time.monotonic()
        st.session_state.session = session
        bot = config.get("bot_name", "DecodeBot")
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": welcome_message(bot, __version__),
            }
        ]
    return st.session_state.session


def _run_ml(callable_name: str, session: SessionState, **kwargs):
    """Lazily call an ML handler; surface missing deps instead of crashing."""
    try:
        from decodebot.ml import app_ml
    except ImportError as exc:
        return (
            "Machine Learning Engine dependencies are not installed. "
            "Install with `pip install -r requirements.txt` "
            f"(details: {exc})."
        )
    try:
        handler = getattr(app_ml, callable_name)
        return handler(session, **kwargs) if kwargs else handler(session)
    except Exception as exc:  # noqa: BLE001 — demo UX must never crash the app
        return f"ML error: {exc}"


def _run_recommend(config: dict, raw_command: str) -> str:
    """Lazily call the recommender; surface missing deps instead of crashing."""
    try:
        from decodebot.recommender import app_recommender
    except ImportError as exc:
        return (
            "Recommender Engine dependencies are not installed. "
            "Install with `pip install -r requirements.txt` "
            f"(details: {exc})."
        )
    try:
        return app_recommender.handle_recommend(config, raw_command)
    except Exception as exc:  # noqa: BLE001
        return f"Recommender error: {exc}"


def _run_ocr(image_path: str, psm: int, config: dict):
    """Lazily run OCR and return (result_or_none, rendered, error_message)."""
    try:
        from decodebot.recognition import app_recognition
    except ImportError as exc:
        return (
            None,
            None,
            (
                "OCR Engine Python packages are not installed. "
                "Install with `pip install -r requirements-ocr.txt` "
                f"(details: {exc})."
            ),
        )
    try:
        result = app_recognition.recognize_image(image_path, psm=psm, config=config)
        rendered = app_recognition.render_result(result, plain=True)
        return result, rendered, None
    except Exception as exc:  # noqa: BLE001
        return None, None, f"OCR Error: {exc}"


session = _init_session()
config = session.config
bot_name = config.get("bot_name", "DecodeBot")

with st.sidebar:
    st.markdown(f"## 🤖 {bot_name} AI")
    st.markdown(f"**Version:** `v{__version__}` | **Status:** `Online`")

    st.markdown(
        """
        <div style="margin-bottom: 1rem;">
            <span class="badge badge-rule">100% Rule-Based</span>
            <span class="badge badge-ml">scikit-learn ML</span>
            <span class="badge badge-rec">TF-IDF Matcher</span>
            <span class="badge badge-ocr">Tesseract OCR</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_selection = st.radio(
        "Navigation",
        [
            "💬 Chatbot",
            "📊 ML Playground",
            "💼 Career Recommender",
            "🔍 OCR Recognition",
            "ℹ️ Architecture & About",
        ],
        index=0,
    )

    st.divider()
    st.markdown("### 📈 Live Session Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Messages", session.message_count)
    with col2:
        st.metric("Duration", get_session_duration(session))

    if session.user_name:
        st.info(f"👤 User: **{session.user_name}**")

    if st.button("🔄 Reset Session", use_container_width=True):
        session.reset()
        session.start_time = time.monotonic()
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": reset_message(session.user_name),
            }
        ]
        st.rerun()

    st.divider()
    st.markdown(
        (
            "<small style='color: #666;'>"
            "100% Local & Auditable • No External APIs • "
            "Strict Module Isolation"
            "</small>"
        ),
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# TAB 1: Chatbot
# -----------------------------------------------------------------------------
if tab_selection == "💬 Chatbot":
    st.markdown(
        f"<div class='main-header'>💬 {bot_name} Rule-Based Chatbot</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        (
            "<div class='sub-header'>"
            "Chat brain powered by deterministic pattern rules and intent "
            "classification (zero black-box NLP/LLMs)."
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    st.markdown("**Quick test queries:**")
    pill_cols = st.columns(6)
    sample_queries = [
        "What can you do?",
        "recommend --skills 'Python, SQL, Machine Learning'",
        "train",
        "predict 5.1, 3.5, 1.4, 0.2",
        "stats",
        "tell me a joke",
    ]
    prompt_to_send = None
    for i, query in enumerate(sample_queries):
        with pill_cols[i]:
            if st.button(query, key=f"pill_{i}", use_container_width=True):
                prompt_to_send = query

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Type your message here...") or prompt_to_send

    if user_input:
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        session.last_input = user_input
        intent = classify_intent(user_input, session)

        if intent == Intent.CLEAR:
            st.session_state.chat_messages = []
            session.record_turn(user_input, intent, "[screen cleared]")
            st.rerun()
        elif intent == Intent.RESET:
            session.reset()
            session.start_time = time.monotonic()
            bot_response = get_reset_text()
            session.record_turn(user_input, intent, bot_response)
        elif intent == Intent.EXIT:
            dur = get_session_duration(session)
            bot_response = exit_message(session.message_count, dur)
            session.record_turn(user_input, intent, bot_response)
        else:
            bot_response = dispatch(intent, session)
            session.record_turn(user_input, intent, bot_response)

        st.session_state.chat_messages.append({"role": "assistant", "content": bot_response})
        with st.chat_message("assistant"):
            st.markdown(bot_response)


# -----------------------------------------------------------------------------
# TAB 2: ML Playground
# -----------------------------------------------------------------------------
elif tab_selection == "📊 ML Playground":
    st.markdown(
        "<div class='main-header'>📊 Machine Learning Playground</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        (
            "<div class='sub-header'>"
            "Interactive interface to train, evaluate, compare, and test "
            "classifiers on the benchmark Iris dataset."
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    ml_col1, ml_col2 = st.columns([1, 1])

    with ml_col1:
        st.markdown("### ⚙️ Train & Tune Model")
        with st.form("train_form"):
            classifier_choice = st.selectbox(
                "Classifier Algorithm",
                [
                    "knn",
                    "decision_tree",
                    "logistic_regression",
                    "svm",
                    "random_forest",
                ],
                index=0,
                format_func=classifier_label,
            )
            knn_k_val = st.slider("K Neighbors (for KNN)", min_value=1, max_value=25, value=5)
            scaler_choice = st.selectbox("Feature Scaling", ["standard", "minmax", "none"], index=0)
            test_size_val = st.slider(
                "Test Set Split Ratio",
                min_value=0.1,
                max_value=0.5,
                value=0.2,
                step=0.05,
            )

            train_btn = st.form_submit_button("🚀 Train Model", use_container_width=True)

        if train_btn:
            session.config["classifier_type"] = classifier_choice
            session.config["knn_k"] = knn_k_val
            session.config["scaler_type"] = scaler_choice
            session.config["ml_test_size"] = test_size_val
            session.ml_state.clear()

            with st.spinner("Training classifier..."):
                train_result = _run_ml("handle_train", session)
                eval_result = _run_ml("handle_evaluate", session)

            st.success("Training finished.")
            st.code(train_result, language="text")
            with st.expander("Detailed Evaluation Metrics", expanded=True):
                st.code(eval_result, language="text")

        st.markdown("### 🧪 Actions & Analysis")
        action_cols = st.columns(3)
        with action_cols[0]:
            if st.button("📊 Explore Data", use_container_width=True):
                st.code(_run_ml("handle_explore", session), language="text")
        with action_cols[1]:
            if st.button("📈 Compare All", use_container_width=True):
                with st.spinner("Comparing classifiers..."):
                    st.code(_run_ml("handle_compare", session), language="text")
        with action_cols[2]:
            if st.button("🎯 Tune K", use_container_width=True):
                with st.spinner("Tuning K..."):
                    st.code(_run_ml("handle_tune_k", session), language="text")

    with ml_col2:
        st.markdown("### 🔮 Interactive Classifier Prediction")
        st.markdown("Enter 4 Iris flower measurements (in cm) or choose a preset:")

        preset = st.radio(
            "Presets:",
            [
                "Custom",
                "Iris-Setosa (5.1, 3.5, 1.4, 0.2)",
                "Iris-Versicolor (6.0, 2.7, 5.1, 1.6)",
                "Iris-Virginica (6.9, 3.1, 5.4, 2.1)",
            ],
            horizontal=True,
        )
        defaults = iris_preset_defaults(preset)
        # Key includes preset so Streamlit refreshes widget values on change.
        preset_key = preset.replace(" ", "_")

        p_col1, p_col2 = st.columns(2)
        with p_col1:
            f1 = st.number_input(
                "Sepal Length (cm)",
                min_value=0.0,
                max_value=15.0,
                value=defaults[0],
                step=0.1,
                key=f"f1_{preset_key}",
            )
            f2 = st.number_input(
                "Sepal Width (cm)",
                min_value=0.0,
                max_value=15.0,
                value=defaults[1],
                step=0.1,
                key=f"f2_{preset_key}",
            )
        with p_col2:
            f3 = st.number_input(
                "Petal Length (cm)",
                min_value=0.0,
                max_value=15.0,
                value=defaults[2],
                step=0.1,
                key=f"f3_{preset_key}",
            )
            f4 = st.number_input(
                "Petal Width (cm)",
                min_value=0.0,
                max_value=15.0,
                value=defaults[3],
                step=0.1,
                key=f"f4_{preset_key}",
            )

        if st.button("✨ Predict Class", use_container_width=True):
            features = [f1, f2, f3, f4]
            with st.spinner("Classifying sample..."):
                pred_result = _run_ml("handle_predict", session, features=features)

            st.markdown("#### Prediction Result")
            st.code(pred_result, language="text")

        st.markdown("### 📁 Saved Model Registry")
        if st.button("📋 List Saved Models", use_container_width=True):
            models_table = _run_ml("handle_models", session)
            st.code(models_table, language="text")


# -----------------------------------------------------------------------------
# TAB 3: Career Recommender
# -----------------------------------------------------------------------------
elif tab_selection == "💼 Career Recommender":
    st.markdown(
        "<div class='main-header'>💼 Tech Stack & Career Recommender</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        (
            "<div class='sub-header'>"
            "Content-based recommendation matching user skills against tech "
            "career profiles using TF-IDF and Cosine Similarity."
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    st.markdown("### 🛠️ Enter Your Skills")
    preset_skill_choices = [
        "Python",
        "SQL",
        "Machine Learning",
        "Statistics",
        "Deep Learning",
        "Natural Language Processing",
        "JavaScript",
        "TypeScript",
        "React",
        "Node.js",
        "HTML",
        "CSS",
        "Docker",
        "Kubernetes",
        "CI/CD",
        "Linux",
        "AWS",
        "Git",
        "Java",
        "C++",
    ]

    selected_tags = st.multiselect(
        "Select skills from common keywords:",
        preset_skill_choices,
        default=["Python", "SQL", "Machine Learning"],
    )

    custom_text = st.text_input(
        "Or enter additional freeform skills (comma separated):",
        value="",
        placeholder="e.g. pandas, pytorch, communication, data analysis",
    )

    skills_query = combine_skills(selected_tags, custom_text)
    top_n = st.slider("Number of Top Matches", min_value=1, max_value=5, value=3)

    if st.button("🎯 Recommend Careers", use_container_width=True):
        if not skills_query.strip():
            st.warning("Please select or enter at least one skill.")
        else:
            raw_command = f'recommend --skills "{skills_query}" --top {top_n}'
            with st.spinner("Computing cosine similarities across career corpus..."):
                output_text = _run_recommend(session.config, raw_command)

            st.markdown("### 🏆 Recommended Roles")
            st.code(output_text, language="text")

            with st.expander("ℹ️ How Recommendation Works"):
                st.markdown("""
1. **Skill Normalization:** Canonical abbreviations are resolved
   (e.g. `ml` → `machine learning`, `js` → `javascript`).
2. **Vectorization:** Query and career corpus become TF-IDF vectors
   using a single shared vocabulary.
3. **Ranking:** Profiles are ranked by Cosine Similarity with
   deterministic tie-breaking.
                    """)


# -----------------------------------------------------------------------------
# TAB 4: OCR Recognition
# -----------------------------------------------------------------------------
elif tab_selection == "🔍 OCR Recognition":
    st.markdown(
        "<div class='main-header'>🔍 Image Text Recognition (OCR)</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        (
            "<div class='sub-header'>"
            "Extract text from document images using adaptive thresholding, "
            "deskewing, and Tesseract OCR."
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    st.info(
        "OCR needs the optional Python packages in `requirements-ocr.txt` "
        "and a local Tesseract binary. On Streamlit Community Cloud, "
        "`packages.txt` installs `tesseract-ocr`. Missing deps show a "
        "friendly error — they do not crash the app."
    )

    ocr_col1, ocr_col2 = st.columns([1, 1])

    with ocr_col1:
        st.markdown("### 📥 Select or Upload Image")
        img_source = st.radio(
            "Source:",
            [
                "Use sample fixture image (`samples/sample_text.png`)",
                "Upload an image (PNG/JPG)",
            ],
        )

        image_path = None
        temp_file_to_clean = None

        if img_source.startswith("Use sample"):
            fixture = sample_image_path(Path(__file__).resolve().parent)
            if fixture.is_file():
                image_path = str(fixture)
                st.image(
                    str(fixture),
                    caption="Sample Fixture Image",
                    use_container_width=True,
                )
            else:
                st.warning("Sample image not found on disk.")
        else:
            uploaded = st.file_uploader("Choose an image file", type=["png", "jpg", "jpeg"])
            if uploaded:
                suffix = safe_upload_suffix(uploaded.name)
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded.getvalue())
                    image_path = tmp.name
                    temp_file_to_clean = tmp.name
                st.image(
                    uploaded,
                    caption="Uploaded Image",
                    use_container_width=True,
                )

        psm_val = st.selectbox(
            "Page Segmentation Mode (PSM)",
            [6, 3, 7, 11],
            index=0,
            format_func=psm_label,
        )

        recognize_btn = st.button("🔎 Run Recognition", use_container_width=True)

    with ocr_col2:
        st.markdown("### 📄 Extracted Text & Confidence")
        if recognize_btn:
            if not image_path:
                st.warning("Please choose or upload an image first.")
            else:
                with st.spinner("Processing image and performing OCR..."):
                    raw_result, rendered, err = _run_ocr(image_path, psm_val, session.config)

                try:
                    if err:
                        st.error(err)
                    elif raw_result is not None:
                        if raw_result.status == "accepted":
                            st.success(
                                f"Status: Accepted • " f"Extracted {len(raw_result.words)} words"
                            )
                        elif raw_result.status == "low_confidence":
                            st.warning("Status: Low Confidence")
                        elif raw_result.status == "no_text":
                            st.info("Status: No Text Found")
                        else:
                            st.error(f"Status: Error — {raw_result.message}")

                        st.markdown("#### Extracted Content:")
                        st.text_area(
                            "Full Text",
                            value=raw_result.text or "(no text extracted)",
                            height=180,
                            disabled=True,
                        )

                        st.markdown("#### Structured Terminal Output:")
                        st.code(rendered or "", language="text")
                finally:
                    if temp_file_to_clean and os.path.isfile(temp_file_to_clean):
                        try:
                            os.remove(temp_file_to_clean)
                        except OSError:
                            pass


# -----------------------------------------------------------------------------
# TAB 5: Architecture & About
# -----------------------------------------------------------------------------
elif tab_selection == "ℹ️ Architecture & About":
    st.markdown(
        "<div class='main-header'>ℹ️ Architecture & Design Principles</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        (
            "<div class='sub-header'>"
            "Clean separation of concerns with four decoupled engines and "
            "zero runtime entanglement."
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    st.markdown("""
### 🏛️ System Architecture

```
                     ┌────────────────────────────────────────┐
                     │          Presentation Layer            │
                     │  CLI (main.py) | GUI (Tkinter)         │
                     │  Web App (Streamlit: streamlit_app.py) │
                     └───────────────────┬────────────────────┘
                                         │
                     ┌───────────────────▼────────────────────┐
                     │       DecodeBot Core Brain (W1)        │
                     │  100% Rule-Based Intent Classifier     │
                     │  Session State, History & Config       │
                     └─────────┬──────────────┬───────────────┘
                               │              │
           ┌───────────────────▼───┐      ┌───▼──────────────────┐
           │   ML Engine (W2)      │      │ Recommender (W3)     │
           │   scikit-learn        │      │ TF-IDF & Cosine      │
           │   Supervised Pipeline │      │ Career Matcher       │
           └───────────────────────┘      └──────────────────────┘
                               │
                       ┌───────▼──────────────┐
                       │   OCR Engine (W4)    │
                       │   OpenCV + Tesseract │
                       │   Text Recognition   │
                       └──────────────────────┘
```

### 🛡️ Key Architectural Guarantees
1. **100% Rule-Based Chatbot Core:** Deterministic patterns; no LLM
   hallucinations.
2. **Complete Module Isolation:** ML, Recommender, and OCR stay decoupled
   from the core chatbot loop.
3. **Local Privacy Guarantee:** All computation is local; no network calls
   or telemetry.
4. **Multi-Platform Portability:** Works on Linux, macOS, and Windows
   (including Streamlit Community Cloud).
        """)
