import cv2


IMAGE_FILE    = "parking_lot.png"
OUT_IMAGE     = "parking_lot.png"   # you can change this to, e.g., "parking_lot_with_gates.png"
PREVIEW_WIDTH = 800                # width to downscale for interactive drawing


orig = cv2.imread(IMAGE_FILE)
if orig is None:
    raise FileNotFoundError(f"Could not open {IMAGE_FILE}")

h, w = orig.shape[:2]
scale = PREVIEW_WIDTH / w if w > PREVIEW_WIDTH else 1.0
disp_h, disp_w = int(h * scale), int(w * scale)
disp = cv2.resize(orig, (disp_w, disp_h), interpolation=cv2.INTER_AREA)

# Static display buffer (including all saved rectangles)
base_disp = disp.copy()
img       = base_disp.copy()


for fname in ("parking_entrance_coordinates.txt", "parking_exit_coordinates.txt"):
    open(fname, "w").close()

mode    = "entrance"
ix = iy = 0
drawing = False
coords  = (0,0,0,0)

print("[INFO] Loaded image ({}×{}), drawing at {}×{}".format(w, h, disp_w, disp_h))
print("[INSTRUCTIONS]")
print(" • Drag with left mouse to draw.")
print(" • ENTER to save rect.")
print(" • 'e' to toggle ENTRANCE/EXIT.")
print(" • ESC when done.")
print(f"[MODE] {mode.upper()} gates (red)")


def draw_rect(event, x, y, flags, param):
    global ix, iy, drawing, img, coords
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y
    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        img = base_disp.copy()
        color = (0,0,255) if mode=="entrance" else (255,0,0)
        cv2.rectangle(img, (ix,iy), (x,y), color, 2)
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        coords = (ix, iy, x, y)
        img = base_disp.copy()
        color = (0,0,255) if mode=="entrance" else (255,0,0)
        cv2.rectangle(img, (ix,iy), (x,y), color, 2)

cv2.namedWindow("Parking Gates", cv2.WINDOW_NORMAL)
cv2.setMouseCallback("Parking Gates", draw_rect)


while True:
    cv2.imshow("Parking Gates", img)
    key = cv2.waitKey(1) & 0xFF

    if key == 13:  # ENTER → save
        x1p, y1p, x2p, y2p = coords
        # map back to original image coords
        x1, y1 = int(x1p/scale), int(y1p/scale)
        x2, y2 = int(x2p/scale), int(y2p/scale)

        fname = ("parking_entrance_coordinates.txt"
                 if mode=="entrance" else
                 "parking_exit_coordinates.txt")
        with open(fname, "a") as f:
            f.write(f"{x1} {y1} {x2} {y2}\n")
        print(f"[SAVED] {mode.upper()} gate: ({x1},{y1})→({x2},{y2})")

        # draw permanently onto base_disp at preview scale
        color = (0,0,255) if mode=="entrance" else (255,0,0)
        cv2.rectangle(base_disp, (x1p,y1p), (x2p,y2p), color, 2)
        img = base_disp.copy()

    elif key == ord('e'):  # toggle mode
        mode = "exit" if mode=="entrance" else "entrance"
        print(f"[MODE] now drawing {mode.upper()} gates — {'blue' if mode=='exit' else 'red'} rectangles")

    elif key == 27:  # ESC → done
        print("[INFO] Finished drawing gates.")
        break


# Upscale base_disp back to original and overlay saved rectangles:
annotated = orig.copy()
for fname, color in (
    ("parking_entrance_coordinates.txt", (0,0,255)),
    ("parking_exit_coordinates.txt",     (255,0,0))
):
    with open(fname) as f:
        for line in f:
            x1, y1, x2, y2 = map(int, line.split())
            cv2.rectangle(annotated, (x1,y1), (x2,y2), color, 2)
cv2.imwrite(OUT_IMAGE, annotated)
print(f"[INFO] Wrote annotated image → {OUT_IMAGE}")

cv2.destroyAllWindows()
