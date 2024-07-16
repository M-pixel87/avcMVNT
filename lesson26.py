# This program is meant to show a bunch of different frames of the rgb values broken up

import cv2
import numpy as np

# Load an image
image = cv2.imread('./car.jpg')

# Check if the image was loaded correctly
if image is None:
    raise ValueError("Image not found or path is incorrect")

# Resize the image for smaller width and height
width, height = 200, 200
image_resized = cv2.resize(image, (width, height))

# Split the image into its color channels
blue_channel, green_channel, red_channel = cv2.split(image_resized)

# Create a blank channel (black image) for combining with other channels
blank_channel = np.zeros_like(blue_channel)

# Merge each channel with blank channels to visualize them separately
blue_image = cv2.merge([blue_channel, blank_channel, blank_channel])
green_image = cv2.merge([blank_channel, green_channel, blank_channel])
red_image = cv2.merge([blank_channel, blank_channel, red_channel])

# Concatenate the images horizontally
concatenated_image = np.hstack((image_resized, blue_image, green_image, red_image))

# Display the concatenated image
cv2.imshow('Color Channels', concatenated_image)

# Wait for a key press and close all windows
cv2.waitKey(0)
cv2.destroyAllWindows()
