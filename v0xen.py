import argparse
from PIL import Image
import numpy as np
from scripts.extract import (
    extract_msb, decodeBits, array_conversion, reverse_to_original,
    decode_secret, crop
)
from scripts.embed import (
    save_image, resize_secret, extract_top_4_msbs,
    encode_msbs, process_array, encode_bits, embed
)

class SubcommandHelpFormatter(argparse.RawDescriptionHelpFormatter):
    def _format_action(self, action):
        parts = super()._format_action(action)
        if isinstance(action, argparse._SubParsersAction):
            for cmd, subparser in action.choices.items():
                parts += f"\nSubcommand `{cmd}`:\n"
                parts += subparser.format_help()
        return parts

def embed_mode(args):
    use_rgb = args.rgb
    key = args.key if args.key else " "
    cover_img = Image.open(args.cover).convert("RGB" if use_rgb else "L")
    cover_array = np.array(cover_img)
    if cover_array.ndim == 2:
        cover_array = np.expand_dims(cover_array, axis=-1)
    resized_secret = resize_secret(args.secret, cover_img.width, use_rgb)
    msbs = extract_top_4_msbs(resized_secret)
    encoded = encode_msbs(msbs)
    processed = process_array(encoded,key)
    final_bits = encode_bits(processed)
    stego_array = embed(final_bits, cover_array)
    save_image(stego_array, args.output)
    print(f"Embedding complete in {'RGB' if use_rgb else 'Grayscale'} Mode")
    print(f"Saved stego image to: {args.output}")

def extract_mode(args):
    key = args.key if args.key else " "
    stego = Image.open(args.stego)
    msb_array = extract_msb(stego)
    decoded = decodeBits(msb_array)
    arr_2d = array_conversion(decoded)
    final_array = reverse_to_original(arr_2d,key)
    sec_img = decode_secret(final_array, *stego.size)
    final_img = crop(sec_img)
    final_img.save(args.output)
    print(f"Extraction complete.\nSaved to: {args.output}")

def main():
    parser = argparse.ArgumentParser(
        description=r"v0xen: Image steganography using LSB and music frequencies in Python ¯\_(ツ)_/¯",
        formatter_class=SubcommandHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Choose a mode")

    embed_parser = subparsers.add_parser("embed", help="Embed a secret image into a cover image")
    embed_parser.add_argument("-c", "--cover", required=True, help="Cover image path")
    embed_parser.add_argument("-s", "--secret", required=True, help="Secret image path")
    embed_parser.add_argument("-o", "--output", required=True, help="Stego image output path")
    embed_parser.add_argument("-k", "--key", required=False, help="Secret Key to hide image")
    embed_parser.add_argument("--rgb", "--color", action="store_true", help="Process images in RGB mode (default is grayscale)")
    embed_parser.set_defaults(func=embed_mode)

    extract_parser = subparsers.add_parser("extract", help="Extract a secret image from a stego image")
    extract_parser.add_argument("-s", "--stego", required=True, help="Stego image path")
    extract_parser.add_argument("-o", "--output", required=True, help="Extracted secret image path")
    extract_parser.add_argument("-k", "--key", required=False, help="Secret Key used to embed secret image")
    extract_parser.set_defaults(func=extract_mode)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()