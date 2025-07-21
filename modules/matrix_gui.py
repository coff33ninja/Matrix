#!/usr/bin/env python3
"""
import subprocess
import sys
Basic LED Matrix GUI Controller
Simplified interface for basic matrix control

For advanced features, use: python matrix_controller.py
"""

import tkinter as tk
import threading
import time
import cv2
import numpy as np
from tkinter import filedialog, colorchooser, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageEnhance
import os
import sys

# Import shared modules
from matrix_config import config
from matrix_hardware import hardware

# Matrix dimensions from config
W = int(config.get("matrix_width", 16))
H = int(config.get("matrix_height", 16))

print("=" * 70)
print("NOTICE: This basic controller has been superseded!")
print("=" * 70)
print("The matrix_gui.py has been replaced by a unified matrix_controller.py")
print("that combines all features in one optimized application.")
print("")
print("New unified features in matrix_controller.py:")
print("• Tabbed interface with basic and advanced controls")
print("• System monitoring display")
print("• Advanced animations (fire, plasma, rain)")
print("• Web interface and remote control")
print("• Comprehensive settings and import/export")
print("• Shared configuration and hardware modules")
print("• Better performance and DRY code architecture")
print("")
print("Please use: python matrix_controller.py")
print("=" * 70)

if os.path.exists("matrix_controller.py"):
    response = input("\nStart the unified controller? (y/n): ").lower()
    if response in ["y", "yes"]:
        print("Starting unified controller...")
        os.system("python matrix_controller.py")
        sys.exit(0)
    else:
        print("Continuing with legacy basic controller...")
        print("Note: Consider migrating to matrix_controller.py for:")
        print("• Better performance and stability")
        print("• All features in one application")
        print("• Shared configuration system")
        print("• Future updates and support")
        print("")


# ----------------- comm helpers -----------------
def send_frame(img):
    """Send frame using shared hardware module"""
    try:
        img = img.convert("RGB").resize((W, H), Image.NEAREST)
        matrix_data = np.array(img).reshape((H, W, 3))
        hardware.send_frame(matrix_data)
    except Exception as e:
        print(f"Send error: {e}")

def open_port():
    """Connect using shared hardware module"""
    try:
        hardware.connect(mode=mode.get(), port=port_ent.get())
        messagebox.showinfo("Connection", f"Connected to {port_ent.get()}")
    except Exception as e:
        messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
        print("Connection error:", e)


# ----------------- GUI -----------------
root = tk.Tk()
root.title("PC-Case Matrix Controller")

mode = tk.StringVar(value="USB")  # USB / WIFI
tk.Radiobutton(root, text="USB Serial", variable=mode, value="USB").pack(side="left")
tk.Radiobutton(root, text="Wi-Fi ESP32", variable=mode, value="WIFI").pack(side="left")

port_ent = tk.Entry(root, width=10)
port_ent.insert(0, config.get("serial_port"))
port_ent.pack(side="left")
tk.Button(root, text="Connect", command=open_port).pack(side="left")

canvas = tk.Canvas(root, width=W * 20, height=H * 20, bg="black")
canvas.pack()

# off-screen drawing image
draw_img = Image.new("RGB", (W, H), "black")
draw = ImageDraw.Draw(draw_img)


def update_canvas():
    tk_img = ImageTk.PhotoImage(draw_img.resize((W * 20, H * 20), Image.NEAREST))
    canvas.create_image(0, 0, anchor="nw", image=tk_img)
    canvas.image = tk_img


def mouse_paint(ev):
    x, y = ev.x // 20, ev.y // 20
    if 0 <= x < W and 0 <= y < H:
        c = colorchooser.askcolor()[0]
        if c:
            draw.rectangle([x, y, x + 1, y + 1], fill=tuple(int(v) for v in c))
            update_canvas()
            send_frame(draw_img)


canvas.bind("<Button-1>", mouse_paint)


# ----------------- image / video loaders -----------------
def load_image():
    path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.bmp")])
    if path:
        try:
            img = Image.open(path)

            # Enhance image quality using ImageEnhance
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)  # Increase contrast

            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.1)  # Slight sharpening

            draw_img.paste(img.resize((W, H), Image.LANCZOS))
            update_canvas()
            send_frame(draw_img)
            messagebox.showinfo("Success", f"Loaded: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")


def load_gif():
    path = filedialog.askopenfilename(filetypes=[("GIF/MP4", "*.gif *.mp4")])
    if not path:
        return

    def stream():
        cap = cv2.VideoCapture(path)
        while True:
            ok, frame = cap.read()
            if not ok:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            draw_img.paste(img.resize((W, H), Image.LANCZOS))
            root.after(0, update_canvas)
            send_frame(draw_img)
            time.sleep(0.033)  # ≈30 fps

    threading.Thread(target=stream, daemon=True).start()


def clear_matrix():
    """Clear the matrix display"""
    draw.rectangle([0, 0, W, H], fill="black")
    update_canvas()
    send_frame(draw_img)
    messagebox.showinfo("Matrix", "Display cleared")


tk.Button(root, text="Load Image", command=load_image).pack(side="left")
tk.Button(root, text="Play GIF/MP4", command=load_gif).pack(side="left")
tk.Button(root, text="Clear", command=clear_matrix).pack(side="left")

update_canvas()
root.mainloop()
