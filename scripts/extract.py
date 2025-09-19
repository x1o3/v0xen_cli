import librosa
import re
from PIL import Image
import numpy as np
import hashlib

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

mapping = {
    '41': '1111', '42': '1110', '43': '1101', '44': '1100', '45': '1011', 
    '46': '1010', '47': '1001', '30': '1000', '31': '0111', '32': '0110', 
    '33': '0101', '69': '0100', '23': '0011', '2d': '0010'
}

replacements = {
    9: 9, 24: 25, 41: 41, 58: 57, 73: 73, 87: 89, 104: 105, 123: 121, 139: 137,
    156: 153, 165: 169, 185: 185, 196: 201, 220: 217, 233: 233, 247: 249
}

def custom_decode(encoded_str):
    result = []
    segments = encoded_str.split()
    for segment in segments:
        if segment in mapping.values():
            for k, v in mapping.items():
                if v == segment:
                    result.append(k)
                    break
    return ''.join(result)

def crop(img):
    new_width = img.width // 2
    new_height = img.height // 2
    return img.crop((0, 0, new_width, new_height))

def extract_msb(img):
    arr = np.array(img)
    if arr.ndim == 2:
        arr = np.expand_dims(arr, axis=-1)
    return arr & 0b00000011

def decodeBits(msb_array):
    for c in range(msb_array.shape[2]):
        msb_array[:,1::2,c] ^= 0b11
    return msb_array

def array_conversion(extracted_msb_array):
    H, W, C = extracted_msb_array.shape
    new_W = W // 2
    extracted_array = np.zeros((H, new_W, C), dtype=np.uint8)
    for c in range(C):
        for y in range(H):
            high_bits = extracted_msb_array[y, 0::2, c] << 2
            low_bits = extracted_msb_array[y, 1::2, c]
            extracted_array[y, :new_W, c] = high_bits[:new_W] | low_bits[:new_W]
    return extracted_array

def reverse_to_original(extracted_array, key):
    H, W, C = extracted_array.shape
    encoded_array = np.zeros((H, W*3, C), dtype=np.uint8)
    mapping_b = generate_mapping(key=key)
    for c in range(C):
        for y in range(H):
            row = []
            for val in extracted_array[y, :, c]:
                for t, mapped in mapping_b.items():
                    if val == mapped:
                        row.extend(t)
                        break
            while len(row) < W*3:
                row.append(0)
            encoded_array[y, :, c] = row[:W*3]
    return encoded_array

def decode_secret(encoded_array, width, height):
    C = encoded_array.shape[2]
    mode = "RGB" if C == 3 else "L"
    sec_img = Image.new(mode, (width, height))
    
    for c in range(C):
        arr = encoded_array[:,:,c]
        rows, cols = arr.shape
        decoded_rows = []
        for i in range(rows):
            row = []
            for j in range(0, cols-2, 3):
                group = arr[i,j:j+3]
                if len(group) == 3:
                    row.append(' '.join(format(num,'04b') for num in group))
            if row: decoded_rows.append(row)

        hex_array = [[custom_decode(x) for x in r if x.strip()] for r in decoded_rows]
        ascii_array = []
        for r in hex_array:
            row_vals = []
            for hex_str in r:
                try:
                    pairs = [hex_str[i:i+2] for i in range(0,len(hex_str),2)]
                    pairs = [p.replace('69','266f') for p in pairs]
                    s = ''.join(chr(int(p,16)) for p in pairs)
                    notes = re.findall(r'[A-G](?:[#♯b]?[-]?[0-9]*)', s)
                    if notes: row_vals.append(notes)
                except: continue
            if row_vals: ascii_array.append(row_vals)
        
        note_vals = []
        for row in ascii_array:
            r_vals = []
            for notes in row:
                hz = []
                for n in notes:
                    try: hz.append(round(librosa.note_to_hz(n)))
                    except: continue
                if hz: r_vals.append(hz)
            if r_vals: note_vals.append(r_vals)
        
        bin_rows = []
        for row in note_vals:
            r_bin = []
            for hz in row:
                hz = [replacements.get(v,v) for v in hz]
                r_bin.append(' '.join(format(h,'08b') for h in hz))
            if r_bin: bin_rows.append(r_bin)
        
        for y in range(min(height//2,len(bin_rows))):
            for x in range(min(width//2,len(bin_rows[y]))):
                try:
                    pix = int(bin_rows[y][x],2)
                    if mode=="L":
                        sec_img.putpixel((x,y),pix)
                    else:
                        px = list(sec_img.getpixel((x,y)))
                        px[c] = pix
                        sec_img.putpixel((x,y),tuple(px))
                except: 
                    if mode=="L":
                        sec_img.putpixel((x,y),0)
                    else:
                        px = list(sec_img.getpixel((x,y)))
                        px[c]=0
                        sec_img.putpixel((x,y),tuple(px))
    return sec_img