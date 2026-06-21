from ultralytics import YOLO


class AI_YOLO: 
    def __init__(self, model_path='/home/uafs/Downloads/weights(4).engine', conf_threshold=0.5): 
        self.model_path = model_path 
        self.conf_threshold = conf_threshold 
        self.model = None 
        self.class_names = {} 
        try: 
            print(f" Loading YOLO TensorRT model from: {model_path}") 
            self.model = YOLO(model_path) 
            self.class_names = self.model.names 
            print(f" Model loaded successfully ({len(self.class_names)} classes).") 
        except Exception as e: 
            print(f" Error loading YOLO model: {e}") 
            self.model = None 

    def detect(self, frame, display=False): 
        if self.model is None or frame is None: return [] 
        results = self.model(frame, verbose=False) 
        detections = [] 
        for result in results: 
            for box in result.boxes: 
                conf = float(box.conf[0]) 
                if conf < self.conf_threshold: continue 
                x1, y1, x2, y2 = map(float, box.xyxy[0]) 
                cls_id = int(box.cls[0]) 
                label = self.class_names.get(cls_id, f"class_{cls_id}") 
                detections.append({ 
                    "class_id": cls_id, "label": label, "confidence": conf, 
                    "bbox": (int(x1), int(y1), int(x2), int(y2)), 
                    "center": (int((x1+x2)/2), int((y1+y2)/2)), 
                    "width": int(x2 - x1) 
                }) 
        return detections 

    def release(self): 
        pass