from setuptools import setup, find_packages
import sys
import torch

# Determine the numpy version based on Python version
if sys.version_info >= (3, 12):
    numpy_version = "==2.26.4"
else:
    numpy_version = "==1.24.4"

# Determine CUDA availability
cuda_available = torch.cuda.is_available()
torch_version = "torch" if cuda_available else "torch==2.2.0+cpu"
torchaudio_version = "torchaudio" if cuda_available else "torchaudio==2.2.0+cpu"

setup(
    name="SafeGuardianAI",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        f"setuptools==70.0.0",
        f"fastapi==0.114.2",
        f"faster_whisper==0.7.1",
        f"firebase_admin==6.5.0",
        f"geopy==2.4.0",
        f"google-generativeai",
        f"google_api_python_client==2.125.0",
        f"ipython==8.23.0",
        f"jsonschema==4.23.0",
        f"keplergl==0.3.2",
        f"matplotlib==3.9.2",
        f"nexa==1.0",
        f"numpy{numpy_version}",
        f"pandas==2.0.2",
        f"protobuf==5.28.1",
        f"pydantic==2.9.1",
        f"python-dotenv==1.0.1",
        f"python_dateutil==2.9.0.post0",
        f"Requests==2.32.3",
        f"seaborn==0.13.2",
        f"sodapy==2.2.0",
        f"squarify==0.4.3",
        f"stqdm==0.0.5",
        f"streamlit==1.36.0",
        f"streamlit_audiorecorder==0.0.5",
        f"streamlit_extras==0.4.7",
        f"streamlit_geolocation==0.0.10",
        f"streamlit_keplergl==0.3.0",
        f"uvicorn==0.30.6",
        f"WMI==1.5.1",
        f"ctranslate2==3.24.0",
        f"pydub==0.25.1",
        f"firebase-admin",
        f"{torch_version}",
        f"{torchaudio_version}",
    ],
    extras_require={
        "dev": ["pytest", "flake8"],
    },
    python_requires=">=3.11",
)