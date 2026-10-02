import os
import time
import shutil
import subprocess
from pathlib import Path

import streamlit as st
from PIL import Image


MODEL = "./detection/models/YOLO11L_SDA.pt"

TEMP_ROOT = Path("./streamlit_temp")
INPUT_DIR = TEMP_ROOT / "input"
REST_OUTPUT = TEMP_ROOT / "restoration"
CROP_OUTPUT = TEMP_ROOT / "crop"
CLS_OUTPUT = TEMP_ROOT / "classification"
ORDER_OUTPUT = TEMP_ROOT / "ordering"
VIS_OUTPUT = TEMP_ROOT / "visualization"
VIS_IMAGE = VIS_OUTPUT / "visualization.jpg"

DET_OUTPUT = Path("./detection/runs/detect/test_YOLO11L_SDA")


def reset_dirs():
    if TEMP_ROOT.exists():
        shutil.rmtree(TEMP_ROOT)

    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    REST_OUTPUT.mkdir(parents=True, exist_ok=True)
    CROP_OUTPUT.mkdir(parents=True, exist_ok=True)
    CLS_OUTPUT.mkdir(parents=True, exist_ok=True)
    ORDER_OUTPUT.mkdir(parents=True, exist_ok=True)
    VIS_OUTPUT.mkdir(parents=True, exist_ok=True)

    if DET_OUTPUT.exists():
        shutil.rmtree(DET_OUTPUT)


def run_cmd(cmd, step_name, start_time, timer_box):
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    while process.poll() is None:
        elapsed = time.time() - start_time
        timer_box.markdown(f"**Elapsed Time:** {elapsed:.2f} sec")
        time.sleep(0.2)

    stdout, stderr = process.communicate()

    if process.returncode != 0:
        st.error(f"{step_name} failed.")
        st.code(stderr)
        st.stop()

    elapsed = time.time() - start_time
    timer_box.markdown(f"**Elapsed Time:** {elapsed:.2f} sec")

    return stdout


def find_txt_result():
    txt_files = list(ORDER_OUTPUT.glob("*.txt"))
    return txt_files[0] if txt_files else None


def find_image_file(image_dir):
    image_dir = Path(image_dir)
    image_files = (
        list(image_dir.glob("*.jpg")) +
        list(image_dir.glob("*.jpeg")) +
        list(image_dir.glob("*.png")) +
        list(image_dir.glob("*.bmp")) +
        list(image_dir.glob("*.tif")) +
        list(image_dir.glob("*.tiff"))
    )
    return image_files[0] if image_files else None


def find_restored_image():
    return find_image_file(REST_OUTPUT)


def find_input_image():
    return find_image_file(INPUT_DIR)


def find_classification_json():
    json_files = list(CLS_OUTPUT.glob("*.json"))
    return json_files[0] if json_files else None


st.set_page_config(
    page_title="Kuzushiji OCR Demo",
    layout="wide"
)

st.markdown("""
<style>
div.stButton > button {
    background-color: #e8f4fd;
    color: #1f77b4;
    border: 1px solid #b6dffb;
    border-radius: 8px;
    height: 3em;
    font-size: 1rem;
    font-weight: 500;
}

div.stButton > button:hover {
    background-color: #d6ecfc;
    border-color: #8bc4f7;
    color: #1f77b4;
}

div.stButton > button:active {
    background-color: #c7e4fa;
    border-color: #6fb6f2;
    color: #1f77b4;
}
</style>
""", unsafe_allow_html=True)

st.title("A Multi-Stage Framework for Kuzushiji Character Recognition in Japanese Historical Documents")

st.info(
    """
    This application provides an online demonstration of Kuzushiji OCR.
    The detailed implementation and source code are available on our
    [Project Page](https://ruiyangju.github.io/KuzushijiOCR)
    and
    [GitHub Repository](https://github.com/RuiyangJu/Kuzushiji-Character-Recognition).
    """
)

# =========================
# Sidebar Settings
# =========================
st.sidebar.header("Settings")

st.sidebar.markdown("### **Document Restoration**")

enable_restoration = st.sidebar.checkbox(
    "Enable Document Restoration",
    value=True
)

r_min = st.sidebar.slider(
    "R Min",
    min_value=70,
    max_value=120,
    value=90,
    step=5,
    disabled=not enable_restoration
)

rg_ratio = st.sidebar.slider(
    "RG Ratio",
    min_value=1.0,
    max_value=2.0,
    value=1.3,
    step=0.1,
    disabled=not enable_restoration
)

rb_ratio = st.sidebar.slider(
    "RB Ratio",
    min_value=1.0,
    max_value=2.0,
    value=1.3,
    step=0.1,
    disabled=not enable_restoration
)

st.sidebar.divider()

st.sidebar.markdown("### **Visualization**")

font_size = st.sidebar.slider(
    "Visualization Font Size",
    min_value=24,
    max_value=128,
    value=64,
    step=4
)

st.subheader("Upload Image")

uploaded_file = st.file_uploader(
    "",
    type=["png", "jpg", "jpeg", "bmp", "tif", "tiff"],
    label_visibility="collapsed"
)

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")

    with st.container():
        col1, col2 = st.columns(2)

        with col1:
            st.image(
                image,
                caption="Input Image",
                use_container_width=True
            )

        with col2:
            result_placeholder = st.empty()
            result_placeholder.info(
                "Final visualization will be shown here after recognition."
            )

    run_clicked = st.button(
        "Start Recognition",
        use_container_width=True
    )

    log_area = st.container()

    if run_clicked:
        if not os.path.isfile(MODEL):
            st.error(f"Model not found: {MODEL}")
            st.stop()

        reset_dirs()

        input_path = INPUT_DIR / uploaded_file.name
        image.save(input_path)

        start_time = time.time()

        with log_area:
            metric_col1, metric_col2 = st.columns(2)

            timer_box = metric_col1.empty()
            progress_box = metric_col2.empty()
            progress = progress_box.progress(0)

            log_box = st.empty()
            logs = []

            def add_log(message):
                logs.append(message)
                log_box.markdown("\n\n".join(logs))

            timer_box.markdown("**Elapsed Time:** 0.00 sec")

            add_log("Running Character Detection ...")
            run_cmd([
                "python", "./detection/predict.py",
                "--model", MODEL,
                "--source", str(INPUT_DIR)
            ], "Character Detection", start_time, timer_box)
            progress.progress(15)

            if enable_restoration:
                add_log("Running Document Restoration ...")
                run_cmd([
                    "python", "./restoration/run.py",
                    "--input_dir", str(INPUT_DIR),
                    "--output_dir", str(REST_OUTPUT),
                    "--r_min", str(r_min),
                    "--rg_ratio", str(rg_ratio),
                    "--rb_ratio", str(rb_ratio)
                ], "Document Restoration", start_time, timer_box)

                crop_image_dir = REST_OUTPUT
                visualization_image = find_restored_image()
            else:
                add_log("Skipping Document Restoration ...")
                crop_image_dir = INPUT_DIR
                visualization_image = find_input_image()

            progress.progress(30)

            add_log("Running Character Cropping ...")
            run_cmd([
                "python", "./crop/run.py",
                "--image_dir", str(crop_image_dir),
                "--labels_dir", str(DET_OUTPUT / "labels"),
                "--save_root", str(CROP_OUTPUT)
            ], "Character Cropping", start_time, timer_box)
            progress.progress(50)

            add_log("Running Character Classification ...")
            run_cmd([
                "python", "./classification/run.py",
                "--root_dir", str(CROP_OUTPUT / "crops"),
                "--out_dir", str(CLS_OUTPUT)
            ], "Character Classification", start_time, timer_box)
            progress.progress(70)

            add_log("Running Character Ordering ...")
            run_cmd([
                "python", "./ordering/run_ours.py",
                "--input_dir", str(CLS_OUTPUT),
                "--output_dir", str(ORDER_OUTPUT)
            ], "Character Ordering", start_time, timer_box)
            progress.progress(85)

            cls_json = find_classification_json()

            add_log("Running Final Visualization ...")

            if visualization_image is not None and cls_json is not None:
                run_cmd([
                    "python", "./visual.py",
                    "--image", str(visualization_image),
                    "--json", str(cls_json),
                    "--out", str(VIS_IMAGE),
                    "--font_size", str(font_size)
                ], "Final Visualization", start_time, timer_box)
            else:
                st.warning(
                    "Visualization image or classification JSON not found. "
                    "Visualization skipped."
                )

            progress.progress(100)

            total_time = time.time() - start_time
            timer_box.markdown(f"**Elapsed Time:** {total_time:.2f} sec")
            add_log(f"Pipeline finished in {total_time:.2f} seconds.")

        if VIS_IMAGE.exists():
            result_placeholder.image(
                str(VIS_IMAGE),
                caption="Final Visualization",
                use_container_width=True
            )
        else:
            result_placeholder.warning("No final visualization found.")

        st.subheader("Recognition Result")

        txt_file = find_txt_result()

        if txt_file is not None:
            result_text = txt_file.read_text(encoding="utf-8")

            st.text_area(
                "",
                result_text,
                height=300,
                label_visibility="collapsed"
            )

            st.download_button(
                label="Download Recognition TXT",
                data=txt_file.read_bytes(),
                file_name=txt_file.name,
                mime="text/plain"
            )
        else:
            st.warning("No recognition txt result found.")

        if VIS_IMAGE.exists():
            st.download_button(
                label="Download Visualization Image",
                data=VIS_IMAGE.read_bytes(),
                file_name="visualization.jpg",
                mime="image/jpeg"
            )
