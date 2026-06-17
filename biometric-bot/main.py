import io
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

print("NEW CODE LOADED ✅")

# Try to import mediapipe
try:
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision as mp_vision
    MEDIAPIPE_AVAILABLE = True
    print("MediaPipe available ✅")
except Exception as e:
    MEDIAPIPE_AVAILABLE = False
    print(f"MediaPipe NOT available — {e}")

app = FastAPI(title="Biometric Privacy Filter API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def encode_image_to_bytes(image: np.ndarray) -> bytes:
    success, encoded_image = cv2.imencode(".jpg", image)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to encode image.")
    return encoded_image.tobytes()


# MediaPipe fingertip landmark IDs
# 4=thumb tip, 8=index tip, 12=middle tip, 16=ring tip, 20=pinky tip
FINGERTIP_IDS = [4, 8, 12, 16, 20]


def get_fingertips_mediapipe(img):
    h, w = img.shape[:2]
    import urllib.request, os, tempfile

    # Download model if not present
    model_path = os.path.join(tempfile.gettempdir(), "hand_landmarker.task")
    if not os.path.exists(model_path):
        print("Downloading hand landmarker model...")
        urllib.request.urlretrieve(
            "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
            model_path
        )
        print("Model downloaded ✅")

    BaseOptions = mp_python.BaseOptions
    HandLandmarker = mp_vision.HandLandmarker
    HandLandmarkerOptions = mp_vision.HandLandmarkerOptions

    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        num_hands=2,
        min_hand_detection_confidence=0.3,
        min_tracking_confidence=0.3
    )

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)

    with HandLandmarker.create_from_options(options) as detector:
        result = detector.detect(mp_image)

    if not result.hand_landmarks:
        return None

    FINGERTIP_IDS = [4, 8, 12, 16, 20]
    fingertips = []
    for hand in result.hand_landmarks:
        for tip_id in FINGERTIP_IDS:
            lm = hand[tip_id]
            cx = max(0, min(w - 1, int(lm.x * w)))
            cy = max(0, min(h - 1, int(lm.y * h)))
            fingertips.append((cx, cy))

    return fingertips if fingertips else None



# ── Fallback (no MediaPipe) ───────────────────────────────────────────────────

def is_likely_hand(contour, img_shape):
    h, w = img_shape[:2]
    area = cv2.contourArea(contour)
    if area < (w * h * 0.03):
        return False
    hx, hy, hw, hh = cv2.boundingRect(contour)
    aspect = hh / hw if hw > 0 else 0
    if aspect < 0.5 or aspect > 4.0:
        return False
    hull = cv2.convexHull(contour)
    hull_area = cv2.contourArea(hull)
    if hull_area == 0:
        return False
    solidity = area / hull_area
    if solidity < 0.4 or solidity > 0.97:
        return False
    return True


def detect_skin_contour(img):
    hsv   = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    m1 = cv2.inRange(hsv,   np.array([0,  15,  60]), np.array([25, 255, 255]))
    m2 = cv2.inRange(hsv,   np.array([165,15,  60]), np.array([180,255, 255]))
    m3 = cv2.inRange(ycrcb, np.array([0, 135,  85]), np.array([255,180, 135]))
    skin = cv2.bitwise_or(cv2.bitwise_or(m1, m2), m3)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    skin = cv2.morphologyEx(skin, cv2.MORPH_CLOSE, k)
    skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN,  k)
    contours, _ = cv2.findContours(skin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return max(contours, key=cv2.contourArea) if contours else None


def try_segment_hand(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))

    c = detect_skin_contour(img)
    if c is not None and is_likely_hand(c, img.shape):
        return c

    for thresh_val, inv in [(200, True), (0, True)]:
        if thresh_val == 0:
            _, m = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        else:
            flag = cv2.THRESH_BINARY_INV if inv else cv2.THRESH_BINARY
            _, m = cv2.threshold(gray, thresh_val, 255, flag)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN,  k)
        contours, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if contours:
            c = max(contours, key=cv2.contourArea)
            if is_likely_hand(c, img.shape):
                return c
    return None


def find_fingertips_contour(contour, img_shape):
    h, w = img_shape[:2]
    pts = contour[:, 0, :]
    n = len(pts)
    if n < 20:
        return []

    smooth_k = max(5, n // 30)
    if smooth_k % 2 == 0:
        smooth_k += 1
    y_smooth = np.convolve(pts[:, 1].astype(float),
                           np.ones(smooth_k) / smooth_k, mode='same')
    window = max(15, n // 12)
    raw_tips = []
    for i in range(n):
        l = list(range(max(0, i - window), i))
        r = list(range(i + 1, min(n, i + window + 1)))
        if not l or not r:
            continue
        if y_smooth[i] < np.min(y_smooth[l]) and y_smooth[i] < np.min(y_smooth[r]):
            raw_tips.append((int(pts[i][0]), int(pts[i][1])))

    hx, hy, hw, hh = cv2.boundingRect(contour)
    raw_tips = [(x, y) for x, y in raw_tips if y < hy + hh * 0.65]

    min_dist = max(20, hw * 0.10)
    filtered = []
    for ft in sorted(raw_tips, key=lambda p: p[1]):
        if all(np.linalg.norm(np.array(ft) - np.array(ex)) > min_dist for ex in filtered):
            filtered.append(ft)
        if len(filtered) == 5:
            break
    return filtered

# ─────────────────────────────────────────────────────────────────────────────

def smart_fingerprint_blur(roi):
    blurred = cv2.GaussianBlur(roi, (7, 7), 2)
    noise   = np.random.normal(0, 8, roi.shape).astype(np.int16)
    noisy   = np.clip(blurred.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    result  = cv2.bilateralFilter(noisy, d=9, sigmaColor=40, sigmaSpace=40)
    return cv2.addWeighted(result, 0.70, roi, 0.30, 0)


def draw_subtle_circle(img, center, radius):
    overlay = img.copy()
    cv2.circle(overlay, center, radius, (0, 0, 200), 1)
    cv2.circle(overlay, center, 3, (0, 200, 0), -1)
    cv2.addWeighted(overlay, 0.4, img, 0.6, 0, img)


@app.post("/protect-biometrics")
async def protect_biometrics(file: UploadFile = File(...)):
    contents = await file.read()
    nparr   = np.frombuffer(contents, np.uint8)
    img     = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file.")

    h, w = img.shape[:2]
    protected_img         = img.copy()
    original_with_warnings = img.copy()

    fingertips = None
    hw_ref = w // 3  # fallback hand width reference

    # ── Step 1: Get fingertips ────────────────────────────────────────────────
    if MEDIAPIPE_AVAILABLE:
        fingertips = get_fingertips_mediapipe(img)
        if fingertips:
            # Estimate hand width from landmark spread for radius scaling
            xs = [p[0] for p in fingertips]
            hw_ref = max(xs) - min(xs) if len(xs) > 1 else w // 3

    # Fallback to contour method if MediaPipe failed or unavailable
    if not fingertips:
        hand_contour = try_segment_hand(img)
        if hand_contour is None:
            # No hand at all — return original unchanged
            combined   = np.hstack((img, img))
            img_bytes  = encode_image_to_bytes(combined)
            return StreamingResponse(io.BytesIO(img_bytes), media_type="image/jpeg")

        hx, hy, hw_c, hh = cv2.boundingRect(hand_contour)
        hw_ref     = hw_c
        fingertips = find_fingertips_contour(hand_contour, img.shape)

        if not fingertips:
            # Last resort: top of each column
            cols   = 5
            col_w  = hw_c // cols
            fingertips = [
                (hx + col_w * i + col_w // 2, hy + int(hh * 0.10))
                for i in range(cols)
            ]

    # ── Step 2: Blur + mark each fingertip ───────────────────────────────────
    for (cx, cy) in fingertips:
        radius = max(15, int(hw_ref * 0.10))  # covers fingertip pad

        x1 = max(0, cx - radius)
        y1 = max(0, cy - radius)
        x2 = min(w, cx + radius)
        y2 = min(h, cy + radius)

        roi = protected_img[y1:y2, x1:x2]
        if roi.size == 0:
            continue

        protected_img[y1:y2, x1:x2] = smart_fingerprint_blur(roi)
        draw_subtle_circle(original_with_warnings, (cx, cy), max(8, int(hw_ref * 0.05)))

    # ── Step 3: Return ────────────────────────────────────────────────────────
    combined  = np.hstack((original_with_warnings, protected_img))
    img_bytes = encode_image_to_bytes(combined)
    return StreamingResponse(io.BytesIO(img_bytes), media_type="image/jpeg")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)