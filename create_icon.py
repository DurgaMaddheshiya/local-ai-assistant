"""
Create a simple ICO file for the application
"""
from PIL import Image, ImageDraw
import os

# Create a simple robot emoji-like icon
size = 256
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Background circle (light blue)
draw.ellipse([10, 10, size-10, size-10], fill=(37, 99, 235, 255))

# Robot head (darker blue)
head_bbox = [50, 60, 206, 180]
draw.rectangle(head_bbox, fill=(59, 130, 246, 255))

# Eyes
eye_left = [80, 90, 100, 110]
eye_right = [156, 90, 176, 110]
draw.ellipse(eye_left, fill=(255, 255, 255, 255))
draw.ellipse(eye_right, fill=(255, 255, 255, 255))

# Pupils
pupil_left = [85, 95, 95, 105]
pupil_right = [161, 95, 171, 105]
draw.ellipse(pupil_left, fill=(37, 99, 235, 255))
draw.ellipse(pupil_right, fill=(37, 99, 235, 255))

# Mouth (simple line)
draw.line([(80, 140), (176, 140)], fill=(255, 255, 255, 255), width=3)

# Antenna (simple lines)
draw.line([(128, 50), (128, 20)], fill=(59, 130, 246, 255), width=4)
draw.ellipse([118, 10, 138, 30], fill=(59, 130, 246, 255))

# Save as ICO
img.save('installer_icon.ico')
print("✓ Icon created: installer_icon.ico")
