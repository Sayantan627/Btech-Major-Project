import cv2
from os import path
from parking_availability import parking_availability
import distance_calc

def load_coordinates(filename):
    """Utility to read rectangles from a txt file (one x1 y1 x2 y2 per line)."""
    coords = []
    try:
        with open(filename) as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 4:
                    coords.append(tuple(map(int, parts)))
    except FileNotFoundError:
        pass
    return coords

print("-" * 50)
print("SMART PARKING SYSTEM".center(50))
print("-" * 50)

# ─── SETUP PHASE ───────────────────────────────────────────────────────────────
while True:
    print()
    print("Enter your option:")
    print("1. Capture new parking area")
    print("2. Use saved parking area")
    choice = int(input("Choose: "))

    if choice == 1:
        import capture_parking_lot
        print()
        print("Display captured parking area?")
        print("1. Yes")
        print("2. No")
        sub = int(input("Choose: "))
        if sub == 1:
            import display_captured_parking_lot
        else:
            print("[INFO] Skip display parking area.")
        print("[INFO] Please draw parking area.")
        import draw_parking_area
        print("[STATUS] Complete drawing parking area.")
        import label_parking_lot
        print("[STATUS] Complete labeling parking slots.")
        print("[INFO] Please draw parking gates (entrances & exits).")
        import draw_parking_gates   # your combined draw for both IN & OUT
        print("[STATUS] Complete drawing parking gates.")
        break

    else:
        print("[ERROR] No parking area found, please capture new parking area.")


camera = cv2.VideoCapture(1)
print("[INFO] Initializing camera.")
cv2.namedWindow("Camera")

car_cascade = cv2.CascadeClassifier('cars.xml')  # Haar cascade for car detection


try:
    with open("parking_labels.txt") as f:
        labels = f.read().splitlines()
except FileNotFoundError:
    print("[WARNING] parking_labels.txt not found.")
    labels = []

entrances = load_coordinates("parking_entrance_coordinates.txt")
exits     = load_coordinates("parking_exit_coordinates.txt")

parking_lot_coords = []
try:
    with open("parking_area_coordinates.txt") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 4:
                parking_lot_coords.append(tuple(map(int, parts)))
except FileNotFoundError:
    print("[ERROR] parking_area_coordinates.txt not found.")
    exit(1)

prev_car_in_entrance = False
prev_unavailable_set = set()


while True:
    ret, frame = camera.read()
    if not ret:
        print("[ERROR] Failed to read from camera.")
        break

    # 1. Detect cars in frame
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cars = car_cascade.detectMultiScale(gray_frame, 1.1, 5)

    # 2. Check if any car is inside an entrance region
    car_in_entrance = False
    for (x,y,w,h) in cars:
        cx, cy = x + w//2, y + h//2
        for (ex1,ey1,ex2,ey2) in entrances:
            if ex1 < cx < ex2 and ey1 < cy < ey2:
                car_in_entrance = True
                break
        if car_in_entrance:
            break

    # 3. Draw all entrances (red) & exits (blue)
    for (x1, y1, x2, y2) in entrances:
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 1)
        cv2.putText(frame, "IN",
                    (x1 + (x2-x1)//2 - 5, y1 + (y2-y1)//2 + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    for (x1, y1, x2, y2) in exits:
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 1)
        cv2.putText(frame, "OUT",
                    (x1 + (x2-x1)//2 - 8, y1 + (y2-y1)//2 + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

    # 4. Label each parking slot green/red
    for idx, (x1, y1, x2, y2) in enumerate(parking_lot_coords):
        slot_roi = frame[y1:y2, x1:x2]
        free, _ = parking_availability(slot_roi)  # returns (1=free,0=occupied)
        color = (0,255,0) if free==1 else (0,0,255)
        cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)
        label = labels[idx] if idx < len(labels) else str(idx)
        cv2.putText(frame, label,
                    (x1 + 5, y2 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)

    # 5. Get full-frame availability
    available, unavailable = parking_availability(frame)

    # 6. Highlight occupied in solid red
    for (x1, y1, x2, y2) in unavailable:
        cv2.rectangle(frame, (x1,y1), (x2,y2), (0,0,255), 1)

    # 7. **ENTRY** — show nearest parking **only** while car is in entrance
    if car_in_entrance:
        best_dist = float('inf')
        closest_parking = None
        for ent in entrances:
            cand = distance_calc.find_closest_parking(parking_list=available, entrance=ent)
            d = distance_calc.calculate_distance(cand, ent)
            if d < best_dist:
                best_dist = d
                closest_parking = cand

        if closest_parking:
            x1,y1,x2,y2 = closest_parking
            cv2.rectangle(frame, (x1,y1), (x2,y2), (255,0,255), 2)
            meters = best_dist / 40.0
            secs   = round(meters / 2.5, 2)
            idx    = parking_lot_coords.index(closest_parking)
            lbl    = labels[idx] if idx < len(labels) else str(idx)
            cv2.putText(frame,
                        f"--> Nearest Parking: {lbl} ({meters:.2f}m, {secs}s)",
                        (10, frame.shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,255), 2)

    # 8. **EXIT** — detect freed slots and show nearest exit gate
    curr_unavail_set = set(map(tuple, unavailable))
    freed = prev_unavailable_set - curr_unavail_set
    for slot in freed:
        # find nearest exit to this freed slot
        exit_rect = distance_calc.find_closest_parking(parking_list=exits, entrance=slot)
        d_exit = distance_calc.calculate_distance(slot, exit_rect)
        meters_exit = d_exit / 40.0
        secs_exit   = round(meters_exit / 2.5, 2)
        # highlight exit
        ex1,ey1,ex2,ey2 = exit_rect
        cv2.rectangle(frame, (ex1,ey1), (ex2,ey2), (0,255,255), 2)
        idx_e = exits.index(exit_rect)
        cv2.putText(frame,
                    f"<-- Nearest Exit: {idx_e+1} ({meters_exit:.2f}m, {secs_exit}s)",
                    (10, frame.shape[0] - 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 2)

    prev_unavailable_set = curr_unavail_set

    # 9. Show
    disp = cv2.resize(frame,
                      (int(frame.shape[1]*0.6), int(frame.shape[0]*0.6)),
                      interpolation=cv2.INTER_AREA)
    cv2.imshow("Camera", disp)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        print("[INFO] Camera terminated.")
        break

camera.release()
cv2.destroyAllWindows()
