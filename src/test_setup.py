# test_setup.py
# Run this to confirm everything is installed correctly

print("Testing all imports...")

import easyocr
print("EasyOCR - OK")

import torch
print("PyTorch - OK")
print("GPU available:", torch.cuda.is_available())

from transformers import pipeline
print("Transformers - OK")

import streamlit
print("Streamlit - OK")

import pandas
print("Pandas - OK")

print("\nAll good! Your setup is complete.")