import cv2

IMAGE_FILE     = "parking_lot.png"
COORDS_FILE    = "parking_area_coordinates.txt"
PREVIEW_WIDTH  = 800   # max width of the interactive window


orig = cv2.imread(IMAGE_FILE)
if orig is None:
    raise FileNotFoundError(f"Could not open {IMAGE_FILE}")

h, w = orig.shape[:2]
scale = PREVIEW_WIDTH / w if w > PREVIEW_WIDTH else 1.0
disp_size = (int(w * scale), int(h * scale))
disp = cv2.resize(orig, disp_size, interpolation=cv2.INTER_AREA)

# one‐time clear & base buffer
open(COORDS_FILE, "w").close()
base_disp = disp.copy()
img       = base_disp.copy()

print("[INFO] Drawing parking areas at {}×{} (orig {}×{})".format(
    disp_size[0], disp_size[1], w, h))
print("[INSTRUCTIONS]")
print(" • Drag left‐mouse to draw a rectangle.")
print(" • Press ENTER to save the current area.")
print(" • Press ESC to finish.\n")

ix = iy = 0
drawing = False
coords = (0, 0, 0, 0)
lot_count = 0


def draw_rectangle(event, x, y, flags, param):
    global ix, iy, drawing, img, coords
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y

    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        img = base_disp.copy()
        cv2.rectangle(img, (ix, iy), (x, y), (0,255,0), 2)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        coords = (ix, iy, x, y)
        img = base_disp.copy()
        cv2.rectangle(img, (ix, iy), (x, y), (0,255,0), 2)

cv2.namedWindow("Parking area", cv2.WINDOW_NORMAL)
cv2.setMouseCallback("Parking area", draw_rectangle)


while True:
    cv2.imshow("Parking area", img)
    key = cv2.waitKey(1) & 0xFF

    if key == 13:  # ENTER
        x1p, y1p, x2p, y2p = coords
        # map back to original coords
        x1, y1 = int(x1p/scale), int(y1p/scale)
        x2, y2 = int(x2p/scale), int(y2p/scale)

        lot_count += 1
        print(f"[INFO] Saved parking area #{lot_count}: ({x1},{y1})→({x2},{y2})")

        # write to coords file
        with open(COORDS_FILE, "a") as f:
            f.write(f"{x1} {y1} {x2} {y2}\n")

        # draw permanently into our preview buffer
        cv2.rectangle(base_disp, (x1p, y1p), (x2p, y2p), (0,255,0), 2)
        img = base_disp.copy()

    elif key == 27:  # ESC
        print("[INFO] Finished drawing parking areas.")
        break


annotated = orig.copy()
with open(COORDS_FILE) as f:
    for line in f:
        x1, y1, x2, y2 = map(int, line.split())
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0,255,0), 2)
cv2.imwrite(IMAGE_FILE, annotated)
print(f"[INFO] Overwrote {IMAGE_FILE} with drawn areas.")

cv2.destroyAllWindows()
