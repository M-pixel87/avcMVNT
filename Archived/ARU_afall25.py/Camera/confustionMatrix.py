import jetson.inference
import jetson.utils
import os
import numpy as np
from sklearn.metrics import confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

def calculate_iou(box1, box2):
    # box format: (x1, y1, x2, y2)
    x1_inter = max(box1[0], box2[0])
    y1_inter = max(box1[1], box2[1])
    x2_inter = min(box1[2], box2[2])
    y2_inter = min(box1[3], box2[3])

    inter_area = max(0, x2_inter - x1_inter) * max(0, y2_inter - y1_inter)

    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])

    union_area = box1_area + box2_area - inter_area

    iou = inter_area / union_area if union_area > 0 else 0
    return iou

# --- Configuration ---
MODEL_PATH = "path/to/your/model.onnx"
LABELS_PATH = "path/to/your/labels.txt"
TEST_IMAGE_DIR = "path/to/your/test/images/"
ANNOTATION_DIR = "path/to/your/test/annotations/"
CONFIDENCE_THRESHOLD = 0.5
IOU_THRESHOLD = 0.5

# --- Load Model and Class Labels ---
net = jetson.inference.detectNet(MODEL_PATH, LABELS_PATH, threshold=CONFIDENCE_THRESHOLD)
with open(LABELS_PATH, 'r') as f:
    class_names = [line.strip() for line in f.readlines()]

y_true = []
y_pred = []

# --- Process each image in the test set ---
for image_filename in os.listdir(TEST_IMAGE_DIR):
    if not image_filename.endswith((".jpg", ".jpeg", ".png")):
        continue

    image_path = os.path.join(TEST_IMAGE_DIR, image_filename)
    annotation_path = os.path.join(ANNOTATION_DIR, os.path.splitext(image_filename)[0] + ".txt")

    # --- Run Inference ---
    img = jetson.utils.loadImage(image_path)
    detections = net.Detect(img)

    # --- Get Ground Truth Annotations ---
    ground_truths = []
    if os.path.exists(annotation_path):
        with open(annotation_path, 'r') as f:
            for line in f.readlines():
                parts = line.strip().split()
                class_id = int(parts[0])
                x_center, y_center, width, height = map(float, parts[1:])
                x1 = (x_center - width / 2) * img.width
                y1 = (y_center - height / 2) * img.height
                x2 = (x_center + width / 2) * img.width
                y2 = (y_center + height / 2) * img.height
                ground_truths.append({'class_id': class_id, 'bbox': [x1, y1, x2, y2], 'detected': False})

    # --- Match Predictions with Ground Truth ---
    for det in detections:
        det_bbox = (det.Left, det.Top, det.Right, det.Bottom)
        best_iou = 0
        best_gt_idx = -1

        for i, gt in enumerate(ground_truths):
            iou = calculate_iou(det_bbox, gt['bbox'])
            if iou > best_iou:
                best_iou = iou
                best_gt_idx = i

        if best_iou > IOU_THRESHOLD:
            if ground_truths[best_gt_idx]['class_id'] == det.ClassID:
                if not ground_truths[best_gt_idx]['detected']:
                    y_true.append(class_names[ground_truths[best_gt_idx]['class_id']])
                    y_pred.append(class_names[det.ClassID])
                    ground_truths[best_gt_idx]['detected'] = True
            else:
                # Misclassification
                y_true.append(class_names[ground_truths[best_gt_idx]['class_id']])
                y_pred.append(class_names[det.ClassID])
        else:
            # False Positive (detected object with no corresponding ground truth)
            y_true.append('background') # Or some other placeholder for no-object
            y_pred.append(class_names[det.ClassID])

    # --- Account for False Negatives (missed ground truth objects) ---
    for gt in ground_truths:
        if not gt['detected']:
            y_true.append(class_names[gt['class_id']])
            y_pred.append('background') # Or some other placeholder for missed detection

# --- Generate and Plot Confusion Matrix ---
all_classes = class_names + ['background']
cm = confusion_matrix(y_true, y_pred, labels=all_classes)

plt.figure(figsize=(12, 10))
sns.heatmap(cm, annot=True, fmt='d', xticklabels=all_classes, yticklabels=all_classes)
plt.xlabel('Predicted')
plt.ylabel('True')
plt.title('Confusion Matrix')
plt.show()
#automated retrival unit
