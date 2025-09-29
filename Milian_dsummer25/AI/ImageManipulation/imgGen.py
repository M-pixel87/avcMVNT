import cv2
import numpy as np
import os
import math

import xml.etree.ElementTree as ET

def rotate_image(image, angle, center=None, scale=1.0):
    """Rotates an image by a given angle."""
    (h, w) = image.shape[:2]
    if center is None:
        center = (w / 2, h / 2)
    
    # Perform the rotation
    M = cv2.getRotationMatrix2D(center, angle, scale)
    rotated = cv2.warpAffine(image, M, (w, h))
    
    return rotated, M

def rotate_bboxes(bboxes, angle, center, h, w):
    """Rotates bounding boxes according to the image rotation."""
    new_bboxes = []
    angle_rad = math.radians(angle)
    
    for (xmin, ymin, xmax, ymax) in bboxes:
        # Get corners of the bounding box
        corners = np.array([
            [xmin, ymin],
            [xmax, ymin],
            [xmax, ymax],
            [xmin, ymax]
        ])
        
        # Rotate corners
        cx, cy = center
        rotated_corners = []
        for x, y in corners:
            x_new = (x - cx) * math.cos(angle_rad) - (y - cy) * math.sin(angle_rad) + cx
            y_new = (x - cx) * math.sin(angle_rad) + (y - cy) * math.cos(angle_rad) + cy
            rotated_corners.append([x_new, y_new])
        
        rotated_corners = np.array(rotated_corners)
        
        # Find new AABB (Axis-Aligned Bounding Box)
        new_xmin = max(0, int(np.min(rotated_corners[:, 0])))
        new_ymin = max(0, int(np.min(rotated_corners[:, 1])))
        new_xmax = min(w, int(np.max(rotated_corners[:, 0])))
        new_ymax = min(h, int(np.max(rotated_corners[:, 1])))
        
        new_bboxes.append((new_xmin, new_ymin, new_xmax, new_ymax))
        
    return new_bboxes

def add_noise(image):
    """Adds Gaussian noise to an image."""
    row, col, ch = image.shape
    mean = 0
    var = 0.1
    sigma = var**0.5
    gauss = np.random.normal(mean, sigma, (row, col, ch))
    gauss = gauss.reshape(row, col, ch)
    noisy = image + image * gauss
    noisy = np.clip(noisy, 0, 255)
    return noisy.astype(np.uint8)

def process_files(image_folder, xml_folder, output_image_folder, output_xml_folder, rotation_angles=[90, 180, 270]):
    """
    Augments images and their corresponding XML annotations.
    """
    # Create output directories if they don't exist
    os.makedirs(output_image_folder, exist_ok=True)
    os.makedirs(output_xml_folder, exist_ok=True)

    image_files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    for image_filename in image_files:
        base_name, ext = os.path.splitext(image_filename)
        xml_filename = base_name + '.xml'
        
        image_path = os.path.join(image_folder, image_filename)
        xml_path = os.path.join(xml_folder, xml_filename)

        if not os.path.exists(xml_path):
            print(f"Warning: XML file not found for {image_filename}, skipping.")
            continue

        # Read image and XML
        image = cv2.imread(image_path)
        if image is None:
            print(f"Warning: Could not read image {image_filename}, skipping.")
            continue
            
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        (h, w) = image.shape[:2]
        center = (w / 2, h / 2)

        # --- Augmentation 1: Noise ---
        noisy_image = add_noise(image)
        noisy_image_filename = f"{base_name}_noise{ext}"
        noisy_xml_filename = f"{base_name}_noise.xml"
        
        # Save noisy image
        cv2.imwrite(os.path.join(output_image_folder, noisy_image_filename), noisy_image)
        
        # Update and save XML for noisy image (bboxes don't change)
        noisy_root = ET.fromstring(ET.tostring(root))
        noisy_root.find('filename').text = noisy_image_filename
        noisy_root.find('path').text = os.path.join(output_image_folder, noisy_image_filename)
        ET.ElementTree(noisy_root).write(os.path.join(output_xml_folder, noisy_xml_filename))

        # --- Augmentation 2: Rotation ---
        for angle in rotation_angles:
            # Get original bboxes
            original_bboxes = []
            for obj in root.findall('object'):
                bndbox = obj.find('bndbox')
                xmin = int(bndbox.find('xmin').text)
                ymin = int(bndbox.find('ymin').text)
                xmax = int(bndbox.find('xmax').text)
                ymax = int(bndbox.find('ymax').text)
                original_bboxes.append((xmin, ymin, xmax, ymax))

            # Rotate image and bboxes
            rotated_image, _ = rotate_image(image, angle, center)
            rotated_bboxes = rotate_bboxes(original_bboxes, angle, center, h, w)
            
            rotated_image_filename = f"{base_name}_rot{angle}{ext}"
            rotated_xml_filename = f"{base_name}_rot{angle}.xml"
            
            # Save rotated image
            cv2.imwrite(os.path.join(output_image_folder, rotated_image_filename), rotated_image)
            
            # Update and save XML for rotated image
            rotated_root = ET.fromstring(ET.tostring(root))
            rotated_root.find('filename').text = rotated_image_filename
            rotated_root.find('path').text = os.path.join(output_image_folder, rotated_image_filename)
            
            for i, obj in enumerate(rotated_root.findall('object')):
                bndbox = obj.find('bndbox')
                new_xmin, new_ymin, new_xmax, new_ymax = rotated_bboxes[i]
                bndbox.find('xmin').text = str(new_xmin)
                bndbox.find('ymin').text = str(new_ymin)
                bndbox.find('xmax').text = str(new_xmax)
                bndbox.find('ymax').text = str(new_ymax)
            
            ET.ElementTree(rotated_root).write(os.path.join(output_xml_folder, rotated_xml_filename))

    print("Augmentation process completed.")


if __name__ == '__main__':
    # --- Configuration ---
    # IMPORTANT: Update these paths to your specific folders
    INPUT_IMAGE_DIR = 'path/to/your/images'
    INPUT_XML_DIR = 'path/to/your/xmls'
    OUTPUT_IMAGE_DIR = 'path/to/output/images'
    OUTPUT_XML_DIR = 'path/to/output/xmls'
    
    # --- Run the process ---
    # Example usage:
    # process_files(
    #     'data/images', 
    #     'data/annotations', 
    #     'data_augmented/images', 
    #     'data_augmented/annotations',
    #     rotation_angles=[45, 90, 135, 180, 225, 270]
    # )
    
    print("Script is ready. Please update the folder paths and uncomment the function call in the `if __name__ == '__main__':` block to run.")
