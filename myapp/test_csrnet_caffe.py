
from pathlib import Path

import cv2
import numpy as np


# ==================================================
# 1. PROJECT PATHS
# ==================================================

BASE_DIR = Path(
    r"C:\Users\GAYATHRI\PycharmProjects\CrowdSense"
)

PROTO = BASE_DIR / "models" / "deploy.prototxt"

WEIGHTS = BASE_DIR / "models" / "shanghaib.caffemodel"

VIDEO = BASE_DIR / "media" / "crowd video.mp4"

OUTPUT_IMAGE = BASE_DIR / "media" / "csrnet_test.jpg"


# ==================================================
# 2. CHECK REQUIRED FILES
# ==================================================

print("=" * 50)
print("CSRNet Crowd Counting Test")
print("=" * 50)

for file_path in [PROTO, WEIGHTS, VIDEO]:

    if not file_path.exists():
        raise FileNotFoundError(
            f"Required file not found: {file_path}"
        )

print("All required files found.")


# ==================================================
# 3. LOAD CSRNet MODEL
# ==================================================

print("\nLoading CSRNet model...")

net = cv2.dnn.readNetFromCaffe(
    str(PROTO),
    str(WEIGHTS)
)

print("CSRNet model loaded successfully!")


# ==================================================
# 4. OPEN VIDEO
# ==================================================

print("\nOpening video...")

cap = cv2.VideoCapture(str(VIDEO))

if not cap.isOpened():
    raise RuntimeError(
        f"Unable to open video: {VIDEO}"
    )

total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps = cap.get(cv2.CAP_PROP_FPS)

print("Total frames:", total_frames)
print("Video FPS:", round(fps, 2))


# ==================================================
# 5. READ ONE FRAME
# ==================================================

success, frame = cap.read()
cap.release()

if not success or frame is None:
    raise RuntimeError(
        "Could not read a frame from the video."
    )

print("Original frame shape:", frame.shape)


# ==================================================
# 6. PREPROCESS FRAME
# ==================================================

# deploy.prototxt specifies:
# Batch size = 1
# Channels = 3
# Height = 224
# Width = 224

resized = cv2.resize(
    frame,
    (224, 224),
    interpolation=cv2.INTER_AREA
)

# OpenCV reads images in BGR format.
# Convert to RGB for this preprocessing test.
rgb = cv2.cvtColor(
    resized,
    cv2.COLOR_BGR2RGB
)

blob = cv2.dnn.blobFromImage(
    rgb,
    scalefactor=1.0,
    size=(224, 224),
    mean=(0, 0, 0),
    swapRB=False,
    crop=False
)

print("Input blob shape:", blob.shape)


# ==================================================
# 7. RUN CSRNet PREDICTION
# ==================================================

print("\nRunning CSRNet prediction...")

net.setInput(blob)

density_map = net.forward()

print("Density map shape:", density_map.shape)


# ==================================================
# 8. CALCULATE ESTIMATED CROWD COUNT
# ==================================================

density = np.squeeze(density_map)

if density.ndim != 2:
    raise RuntimeError(
        f"Unexpected density map shape: {density.shape}"
    )

# Sum the predicted density values.
# This is a model estimate, not a verified actual count.
estimated_count = float(np.sum(density))

print("\n" + "=" * 50)
print("CSRNet PREDICTION RESULT")
print("=" * 50)

print("Estimated crowd count:", round(estimated_count, 2))
print("Approximate rounded count:", round(estimated_count))


# ==================================================
# 9. GENERATE DENSITY HEATMAP
# ==================================================

# Normalize density map for visualization only.
normalized = cv2.normalize(
    density,
    None,
    alpha=0,
    beta=255,
    norm_type=cv2.NORM_MINMAX
).astype(np.uint8)

heatmap_small = cv2.applyColorMap(
    normalized,
    cv2.COLORMAP_JET
)

# Resize heatmap to original video dimensions.
heatmap = cv2.resize(
    heatmap_small,
    (frame.shape[1], frame.shape[0]),
    interpolation=cv2.INTER_LINEAR
)

# Overlay the heatmap on the original frame.
overlay = cv2.addWeighted(
    frame,
    0.60,
    heatmap,
    0.40,
    0
)


# ==================================================
# 10. DISPLAY COUNT ON IMAGE
# ==================================================

label = f"CSRNet Estimated Count: {estimated_count:.2f}"

cv2.putText(
    overlay,
    label,
    (20, 45),
    cv2.FONT_HERSHEY_SIMPLEX,
    0.9,
    (255, 255, 255),
    2,
    cv2.LINE_AA
)

# Save the output image.
saved = cv2.imwrite(
    str(OUTPUT_IMAGE),
    overlay
)

if not saved:
    raise RuntimeError(
        f"Could not save image: {OUTPUT_IMAGE}"
    )

print("\nHeatmap saved successfully:")
print(OUTPUT_IMAGE)


# ==================================================
# 11. OPTIONAL: SHOW OUTPUT IMAGE
# ==================================================

cv2.imshow(
    "CSRNet Crowd Density Heatmap",
    overlay
)

print("\nPress any key on the image window to exit.")

cv2.waitKey(0)
cv2.destroyAllWindows()

print("\nTest completed successfully!")
