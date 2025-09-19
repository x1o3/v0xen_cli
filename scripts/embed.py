import librosa
import numpy as np
import hashlib
from PIL import Image
from numba import njit

def load_image(path, use_rgb=False):
    img = Image.open(path).convert("RGB" if use_rgb else "L")
    arr = np.array(img)
    if arr.ndim == 2:
        arr = np.expand_dims(arr, axis=-1)
    return arr

def save_image(arr, path):
    if arr.shape[2] == 1:
        Image.fromarray(arr[:, :, 0], 'L').save(path)
    else:
        Image.fromarray(arr, 'RGB').save(path)

def resize_secret(secret_path, cover_width, use_rgb=False):
    img = Image.open(secret_path).convert("RGB" if use_rgb else "L")
    aspect_ratio = img.height / img.width
    new_width = cover_width // 2
    new_height = int(new_width * aspect_ratio)
    resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    arr = np.array(resized)
    if arr.ndim == 2:
        arr = np.expand_dims(arr, axis=-1)
    return arr

def extract_top_4_msbs(img_array):
    return (img_array >> 4) & 0b1111

mapping_table = {
    '41': '1111', '42': '1110', '43': '1101', '44': '1100',
    '45': '1011', '46': '1010', '47': '1001', '30': '1000',
    '31': '0111', '32': '0110', '33': '0101', '69': '0100',
    '23': '0011', '2d': '0010'
}

@njit
def int_from_bin(bstr):
    val = 0
    for c in bstr:
        val = (val << 1) | int(c)
    return val

def msb_to_encoded(msb):
    msb_bin = format(msb, '04b')
    hz = int(msb_bin + '1001', 2)
    note = librosa.hz_to_note(hz)
    hex_str = ''.join(f"{ord(c):02x}" for c in note).replace('266f','69')
    result = []
    for i in range(0, len(hex_str), 2):
        result.append(mapping_table.get(hex_str[i:i+2], '0001'))
    while len(result) < 3:
        result.append('0001')
    return [int(b, 2) for b in result[:3]]

def encode_msbs(msb_array):
    H, W, C = msb_array.shape
    encoded = np.zeros((H, W * 3, C), dtype=np.uint8)
    for c in range(C):
        for y in range(H):
            for x in range(W):
                encoded[y, x*3:x*3+3, c] = msb_to_encoded(msb_array[y, x, c])
    return encoded

def generate_mapping(key):
    tuples = [
        (10, 4, 5), (9, 5, 1), (12, 4, 5), (10, 6, 1), (11, 7, 1), (9, 8, 1),
        (15, 4, 7), (14, 6, 1), (9, 4, 6), (13, 4, 5), (12, 6, 1), (12, 2, 7),
        (11, 5, 1), (15, 5, 1), (15, 4, 5), (14, 5, 1)
    ]
    mapping = {}
    used = set()
    for t in sorted(tuples):
        hval = int(hashlib.sha256((key + str(t)).encode()).hexdigest(), 16)
        mapped = hval % 16
        while mapped in used:
            mapped = (mapped + 1) % 16
        used.add(mapped)
        mapping[t] = mapped
    return mapping

def process_array(encoded, key):
    mapping = generate_mapping(key=key)
    H, W, C = encoded.shape
    new_W = (W // 3 + 1) * 2
    processed = np.zeros((H, new_W, C), dtype=np.uint8)
    for c in range(C):
        for y in range(H):
            row = encoded[y, :, c]
            mapped = [mapping.get(tuple(row[i:i+3]), 0) for i in range(0, W, 3)]
            expanded = []
            for m in mapped:
                expanded.extend([(m>>2)&0b11, m&0b11])
            processed[y, :len(expanded), c] = expanded
    return processed

def encode_bits(arr):
    H, W, C = arr.shape
    for c in range(C):
        arr[:, 1::2, c] ^= 0b11
    return arr

def embed(encoded, cover_array):
    H, W, C = encoded.shape
    out = cover_array.copy()
    for c in range(C):
        h, w = min(H, out.shape[0]), min(W, out.shape[1])
        out[:h, :w, c] = (out[:h, :w, c] & 0b11111100) | (encoded[:h, :w, c] & 0b11)
    return out