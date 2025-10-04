import os
import cv2
import random
import xml.etree.ElementTree as ET
import albumentations as A

# --- ⚙️ CONFIGURATION ---

# 1. Define the paths to your input folders
IMAGE_DIR = os.path.join('input', 'images')
ANNOTATION_DIR = os.path.join('input', 'annotations')

# 2. Define the path for the new augmented data
OUTPUT_DIR = 'testOutput'

# 3. How many augmented versions to create for each original image
AUGMENTATIONS_PER_IMAGE = 5

# 4. Define your augmentation pipeline using Albumentations
# This pipeline will apply a small rotation and add some noise.
# The `bbox_params` are crucial for ensuring the bounding boxes are transformed correctly.
transform = A.Compose([
    A.Rotate(limit=20, p=0.8, border_mode=cv2.BORDER_CONSTANT),
    A.GaussNoise(var_limit=(10.0, 50.0), p=0.7),
    A.ISONoise(color_shift=(0.01, 0.05), intensity=(0.1, 0.5), p=0.5),
    A.MultiplicativeNoise(multiplier=(0.9, 1.1), p=0.5)
], bbox_params=A.BboxParams(format='pascal_voc', label_fields=['category_ids']))

# --- SCRIPT LOGIC (No need to change below this line) ---

def main():
    """
    Main function to run the augmentation process.
    """
    # Create output directories if they don't exist
    output_img_dir = os.path.join(OUTPUT_DIR, 'images')
    output_ann_dir = os.path.join(OUTPUT_DIR, 'annotations')
    os.makedirs(output_img_dir, exist_ok=True)
    os.makedirs(output_ann_dir, exist_ok=True)

    # Get a list of all XML annotation files
    xml_files = [f for f in os.listdir(ANNOTATION_DIR) if f.endswith('.xml')]
    total_files = len(xml_files)
    print(f"Found {total_files} annotation files. Starting augmentation...")

    # Process each XML file
    for i, filename in enumerate(xml_files):
        xml_path = os.path.join(ANNOTATION_DIR, filename)

        # Parse the XML file
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Find the image filename
        image_filename = root.find('filename').text
        image_path = os.path.join(IMAGE_DIR, image_filename)

        # Read the image
        if not os.path.exists(image_path):
            print(f"⚠️ Warning: Image not found for {filename}. Skipping.")
            continue
            
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Extract bounding boxes and labels
        bboxes = []
        category_ids = []
        for member in root.findall('object'):
            class_name = member.find('name').text
            
            bndbox = member.find('bndbox')
            xmin = int(bndbox.find('xmin').text)
            ymin = int(bndbox.find('ymin').text)
            xmax = int(bndbox.find('xmax').text)
            ymax = int(bndbox.find('ymax').text)
            
            bboxes.append([xmin, ymin, xmax, ymax])
            category_ids.append(class_name)

        # Generate augmented images
        for j in range(AUGMENTATIONS_PER_IMAGE):
            try:
                # Apply the augmentations
                transformed = transform(image=image, bboxes=bboxes, category_ids=category_ids)
                transformed_image = transformed['image']
                transformed_bboxes = transformed['bboxes']
                transformed_category_ids = transformed['category_ids']

                # Create a new filename
                base_name, ext = os.path.splitext(image_filename)
                new_image_filename = f"{base_name}_aug_{j+1}{ext}"
                new_xml_filename = f"{base_name}_aug_{j+1}.xml"

                # Save the new image
                new_image_path = os.path.join(output_img_dir, new_image_filename)
                cv2.imwrite(new_image_path, cv2.cvtColor(transformed_image, cv2.COLOR_RGB2BGR))

                # Create and save the new XML file
                create_new_xml(root, new_xml_filename, new_image_filename, transformed_bboxes, transformed_category_ids, output_ann_dir)
            
            except Exception as e:
                print(f"❌ Error augmenting {filename}: {e}")
                continue # Skip to the next augmentation if one fails

        print(f"({i+1}/{total_files}) Augmented {filename} -> Created {AUGMENTATIONS_PER_IMAGE} new versions.")

    print("\n✅ Augmentation complete!")
    print(f"New data is available in the '{OUTPUT_DIR}' folder.")

def create_new_xml(original_root, new_filename, new_image_name, new_bboxes, new_labels, output_dir):
    """
    Creates a new XML annotation file based on the transformed bounding boxes.
    """
    # Copy the original tree structure but remove old objects
    new_root = ET.Element(original_root.tag)
    for child in original_root:
        if child.tag != 'object':
            new_child = ET.SubElement(new_root, child.tag)
            new_child.text = child.text
    
    # Update filename
    new_root.find('filename').text = new_image_name
    
    # Add new, transformed object elements
    for bbox, label in zip(new_bboxes, new_labels):
        obj = ET.SubElement(new_root, 'object')
        
        name = ET.SubElement(obj, 'name')
        name.text = label
        
        pose = ET.SubElement(obj, 'pose')
        pose.text = 'Unspecified'
        
        truncated = ET.SubElement(obj, 'truncated')
        truncated.text = '0'
        
        difficult = ET.SubElement(obj, 'difficult')
        difficult.text = '0'
        
        bndbox = ET.SubElement(obj, 'bndbox')
        xmin = ET.SubElement(bndbox, 'xmin')
        xmin.text = str(int(bbox[0]))
        ymin = ET.SubElement(bndbox, 'ymin')
        ymin.text = str(int(bbox[1]))
        xmax = ET.SubElement(bndbox, 'xmax')
        xmax.text = str(int(bbox[2]))
        ymax = ET.SubElement(bndbox, 'ymax')
        ymax.text = str(int(bbox[3]))

    # Write the new XML file
    tree = ET.ElementTree(new_root)
    xml_path = os.path.join(output_dir, new_filename)
    tree.write(xml_path)

if __name__ == "__main__":
    main()