# detector/detector.py
import cv2, time
from parking_availability import parking_availability
import distance_calc

def load_coordinates(fn):
    coords = []
    with open(fn) as f:
        for line in f:
            x1,y1,x2,y2 = map(int, line.split())
            coords.append((x1,y1,x2,y2))
    return coords

class ParkingDetector:
    def __init__(self, cam_idx=1, cascade_path='cars.xml'):
        # camera + cascade
        self.cap = cv2.VideoCapture(cam_idx)
        self.car_cascade = cv2.CascadeClassifier(cascade_path)

        # load all your rectangles
        self.entrances = load_coordinates('detector/parking_entrance_coordinates.txt')
        self.exits     = load_coordinates('detector/parking_exit_coordinates.txt')
        self.slots     = load_coordinates('detector/parking_area_coordinates.txt')

        # keep track of last-seen state & last changed timestamp
        self.prev_unocc = set()
        now = time.time()
        self.last_changed = {i: now for i in range(len(self.slots))}

    def get_status(self):
        """
        Captures one frame, runs your availability logic,
        and returns a dict with:
          - slot_ids:       [0,1,2,…]
          - status:         ["free","occupied",…]
          - last_changed:   [unix_ts, …]
        """
        ret, frame = self.cap.read()
        if not ret:
            # on failure, just return previous
            return self._package()

        # 1) detect cars at entrances (optional for pure status)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _cars = self.car_cascade.detectMultiScale(gray, 1.1, 5)

        # 2) compute free vs occupied slots
        #    parking_availability(frame) -> (available_list, unavailable_list)
        available_rects, unavailable_rects = parking_availability(frame)

        # 3) map rect → slot index
        occ_ids = []
        for rect in unavailable_rects:
            if rect in self.slots:
                occ_ids.append(self.slots.index(rect))

        free_ids = [i for i in range(len(self.slots)) if i not in occ_ids]

        # 4) update last_changed
        now = time.time()
        curr_unocc = set(occ_ids)
        # any slot that changed state?
        for i in range(len(self.slots)):
            was_occ = i in self.prev_unocc
            now_occ = i in curr_unocc
            if was_occ != now_occ:
                self.last_changed[i] = now

        self.prev_unocc = curr_unocc
        self._last_free = free_ids
        self._last_occ  = occ_ids

        return self._package()

    def _package(self):
        return {
            "slot_ids":     list(range(len(self.slots))),
            "status":       ["occupied" if i in self.prev_unocc else "free"
                                for i in range(len(self.slots))],
            "last_changed": [self.last_changed[i] for i in range(len(self.slots))]
        }
