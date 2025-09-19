# V0XEN    
   
Python tool for a steganography technique using LSB and music frequencies.   
- **Payload**: resizess to 0.25 of the cover image  
- **PSNR**: 47+    
- **SSIM**: 0.99+    
- **BER**: >0.065    

PSNR, SSIM, BER tested over 7k+ images with key="s9On31havc13".   

### Usage

```sh
usage: v0xen.py [-h] {embed,extract} ...

positional arguments:
  {embed,extract}  Choose a mode
    embed          Embed a secret image into a cover image
    extract        Extract a secret image from a stego image
```
  
### embed:  
```sh
usage: v0xen.py embed [-h] -c COVER -s SECRET -o OUTPUT [-k KEY] [--rgb]

options:
  -h, --help           show this help message and exit
  -c, --cover          Cover image path
  -s, --secret         Secret image path
  -o, --output         Stego image output path
  -k, --key            Secret Key to hide image
  --rgb, --color       Process images in RGB mode (default is grayscale)
```
    
### extract:  
```sh
 usage: v0xen.py extract [-h] -s STEGO -o OUTPUT [-k KEY]  
  
options:  
  -h, --help           show this help message and exit  
  -s, --stego          Stego image path  
  -o, --output         Extracted secret image path  
  -k, --key            Secret Key used to embed secret image  
```
  
Example : `python v0xen.py extract -s ./rgb.png -o ./out.png -k nyx`  
  
This repo includes an `Images/` directory with a few example cover, secret, and stego images.      
These images are provided for demonstration purposes only.   
 
```sh
nix-shell             ### for bash
nix-shell --run fish  ### for fish
```   
For nix-shell environment, exists a shell.nix which can be enabled using the command above.  
