import cv2
import numpy as np
import os
import math
import xml.etree.ElementTree as ET

# --- Image and Bounding Box Transformation Functions ---

def rotate_image(image, angle):
    """Rotates an image by a given angle without cropping."""
    (h, w) = image.shape[:2]
    center = (w / 2, h / 2)
    
    # Get the rotation matrix
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    
    # Perform the rotation
    rotated_image = cv2.warpAffine(image, M, (w, h))
    return rotated_image

def rotate_bboxes(bboxes, angle, center, h, w):
    """Rotates bounding boxes to match the image rotation."""
    new_bboxes = []
    angle_rad = math.radians(angle)
    cx, cy = center
    
    for (xmin, ymin, xmax, ymax) in bboxes:
        # Define the 4 corners of the bounding box
        corners = np.array([
            [xmin, ymin], [xmax, ymin],
            [xmax, ymax], [xmin, ymax]
        ])
        
        # Rotate each corner
        rotated_corners = []
        for x, y in corners:
            x_new = (x - cx) * math.cos(angle_rad) - (y - cy) * math.sin(angle_rad) + cx
            y_new = (x - cx) * math.sin(angle_rad) + (y - cy) * math.cos(angle_rad) + cy
            rotated_corners.append([x_new, y_new])
        
        rotated_corners = np.array(rotated_corners)
        
        # Create a new axis-aligned bounding box that encloses the rotated corners
        new_xmin = max(0, int(np.min(rotated_corners[:, 0])))
        new_ymin = max(0, int(np.min(rotated_corners[:, 1])))
        new_xmax = min(w, int(np.max(rotated_corners[:, 0])))
        new_ymax = min(h, int(np.max(rotated_corners[:, 1])))
        
        new_bboxes.append((new_xmin, new_ymin, new_xmax, new_ymax))
        
    return new_bboxes

def add_noise(image):
    """Adds random Gaussian noise to an image."""
    # Ensure image is in a floating-point format for noise calculation
    img_float = image.astype(np.float32)
    row, col, ch = img_float.shape
    mean = 0
    # Adjust variance for a reasonable amount of noise
    var = 100 
    sigma = var**0.5
    gauss = np.random.normal(mean, sigma, (row, col, ch))
    gauss = gauss.reshape(row, col, ch)
    
    # Add noise and clip values to be within valid image range [0, 255]
    noisy = img_float + gauss
    noisy = np.clip(noisy, 0, 255)
    return noisy.astype(np.uint8)


# --- Main Processing Function ---

def augment_data(image_folder, xml_folder, output_image_folder, output_xml_folder, rotation_angles=[90, 180, 270]):
    """
    Reads images and XMLs, applies augmentations, and saves the new data.
    """
    # Create the output directories if they don't already exist
    os.makedirs(output_image_folder, exist_ok=True)
    os.makedirs(output_xml_folder, exist_ok=True)

    # Find all image files in the input directory
    image_files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    total_files = len(image_files)
    print(f"Found {total_files} images to augment...")

    for i, image_filename in enumerate(image_files):
        print(f"Processing ({i+1}/{total_files}): {image_filename}")

        # Construct full paths for the image and its corresponding XML file
        base_name, ext = os.path.splitext(image_filename)
        xml_filename = base_name + '.xml'
        image_path = os.path.join(image_folder, image_filename)
        xml_path = os.path.join(xml_folder, xml_filename)

        # Skip if the matching XML file doesn't exist
        if not os.path.exists(xml_path):
            print(f"  -> Warning: XML file not found for {image_filename}, skipping.")
            continue

        # Read the image and XML data
        image = cv2.imread(image_path)
        if image is None:
            print(f"  -> Warning: Could not read image {image_filename}, skipping.")
            continue
            
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        (h, w) = image.shape[:2]
        center = (w / 2, h / 2)

        # === 1. Create a version with added noise ===
        noisy_image = add_noise(image)
        noisy_image_filename = f"{base_name}_noise{ext}"
        noisy_xml_filename = f"{base_name}_noise.xml"
        
        cv2.imwrite(os.path.join(output_image_folder, noisy_image_filename), noisy_image)
        
        # Create a new XML for the noisy image (bounding boxes do not change)
        noisy_root = ET.fromstring(ET.tostring(root))
        noisy_root.find('filename').text = noisy_image_filename
        ET.ElementTree(noisy_root).write(os.path.join(output_xml_folder, noisy_xml_filename))

        # === 2. Create versions with rotations ===
        # Get original bounding boxes from the XML
        original_bboxes = []
        objects = root.findall('object')
        for obj in objects:
            bndbox = obj.find('bndbox')
            xmin = int(bndbox.find('xmin').text)
            ymin = int(bndbox.find('ymin').text)
            xmax = int(bndbox.find('xmax').text)
            ymax = int(bndbox.find('ymax').text)
            original_bboxes.append((xmin, ymin, xmax, ymax))

        for angle in rotation_angles:
            # Rotate the image and the bounding boxes
            rotated_image = rotate_image(image, angle)
            rotated_bboxes = rotate_bboxes(original_bboxes, angle, center, h, w)
            
            # Define new filenames for the rotated data
            rotated_image_filename = f"{base_name}_rot{angle}{ext}"
            rotated_xml_filename = f"{base_name}_rot{angle}.xml"
            
            cv2.imwrite(os.path.join(output_image_folder, rotated_image_filename), rotated_image)
            
            # Create a new XML for the rotated image
            rotated_root = ET.fromstring(ET.tostring(root))
            rotated_root.find('filename').text = rotated_image_filename
            
            # Update the coordinates for each object in the new XML
            for i, obj in enumerate(rotated_root.findall('object')):
                bndbox = obj.find('bndbox')
                new_xmin, new_ymin, new_xmax, new_ymax = rotated_bboxes[i]
                bndbox.find('xmin').text = str(new_xmin)
                bndbox.find('ymin').text = str(new_ymin)
                bndbox.find('xmax').text = str(new_xmax)
                bndbox.find('ymax').text = str(new_ymax)
            
            ET.ElementTree(rotated_root).write(os.path.join(output_xml_folder, rotated_xml_filename))

    print("\n✅ Augmentation process completed successfully!")


# --- Script Execution ---

if __name__ == '__main__':
    #IMPORTANT: Update these paths to your specific folders
    INPUT_IMAGE_DIR = r'C:\Users\hoots\OneDrive\Documents\AVC_Files\Milan\MilanCode\avcMVNT\Milian_dsummer25\AI\ImageManipulation\testImgTest'
    INPUT_XML_DIR = r'C:\Users\hoots\OneDrive\Documents\AVC_Files\Milan\MilanCode\avcMVNT\Milian_dsummer25\AI\ImageManipulation\testAnnotationsTest'
    OUTPUT_IMAGE_DIR = r'C:\Users\hoots\OneDrive\Documents\AVC_Files\Milan\MilanCode\avcMVNT\Milian_dsummer25\AI\ImageManipulation\testOutputImg'
    OUTPUT_XML_DIR = r'C:\Users\hoots\OneDrive\Documents\AVC_Files\Milan\MilanCode\avcMVNT\Milian_dsummer25\AI\ImageManipulation\testOutputXml'
    
    # Define the rotation angles you want to apply
    ROTATION_ANGLES = [10, 15, 20, 345, 350, 355]

    # Run the main function
    augment_data(
        INPUT_IMAGE_DIR, 
        INPUT_XML_DIR, 
        OUTPUT_IMAGE_DIR, 
        OUTPUT_XML_DIR,
        rotation_angles=ROTATION_ANGLES
    )