import cv2

# Load positions of parking spots from coordinates file
def load_parking_positions(file_path="parking_area_coordinates.txt"):
    positions = []
    with open(file_path, "r") as f:
        lines = f.readlines()
        for line in lines:
            coords = list(map(int, line.strip().split()))
            x1, y1, x2, y2 = coords
            positions.append((x1, y1, x2 - x1, y2 - y1))  # (x, y, width, height)
    return positions

def parking_availability(frame=None):
    if frame is None:
        cap = cv2.VideoCapture(1)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            print("[ERROR] Unable to read from camera.")
            return [], []

    # cv2.imshow("Original", frame)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # cv2.imshow("1 - Grayscale", gray)
    blur = cv2.GaussianBlur(gray, (3, 3), 1)
    # cv2.imshow("2 - Gaussian Blur", blur)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 25, 16)
    # cv2.imshow("3 - Adaptive Threshold", thresh)
    median = cv2.medianBlur(thresh, 5)
    # cv2.imshow("4 - Median Blur", median)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated = cv2.dilate(median, kernel, iterations=1)
    # cv2.imshow("5 - Dilated", dilated)

    posList = load_parking_positions()
    available = []
    unavailable = []

    for pos in posList:
        x, y, w, h = pos
        imgCrop = dilated[y:y + h, x:x + w]
        count = cv2.countNonZero(imgCrop)

        if count < 900:
            available.append([x, y, x + w, y + h])
        else:
            unavailable.append([x, y, x + w, y + h])

    return available, unavailable
