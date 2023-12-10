from PIL import Image
import cv2
import io
import numpy as np
import matplotlib.pyplot as plt


def process_image(image_path, conversion_factor, label_mapping, lower_green=(35, 52, 72), upper_green=(102, 255, 255), 
                  min_area=1000, dilation_kernel_size=(50, 50), max_regions=24, grid_size=6, num_columns=4):
    
    """
    Process the image and return processed data.

    Args:
    image_path (str): Path to the image.
    conversion_factor (float): Factor to convert pixel to real-world units.
    label_mapping (dict): Mapping from numeric labels to string labels.
    lower_green (tuple): Lower HSV bound for green color segmentation.
    upper_green (tuple): Upper HSV bound for green color segmentation.
    min_area (int): Minimum area to consider for contour.
    dilation_kernel_size (tuple): Size of the kernel for dilation.
    max_regions (int): Maximum number of regions to process.
    grid_size (int): Number of rows in the output grid.
    num_columns (int): Number of columns in the output grid.

    Returns:
    tuple: Processed image, text data, and verification plot.
    """

    # Load the image
    file_path = image_path
    image = cv2.imread(file_path)

    # Convert to RGB for matplotlib compatibility and HSV for color segmentation
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Threshold the HSV image to get only green colors
    mask = cv2.inRange(image_hsv, lower_green, upper_green)

    # Bitwise-AND mask and original image to isolate the green area
    isolated_green = cv2.bitwise_and(image_rgb, image_rgb, mask=mask)

    # Convert the mask to binary
    binary_mask = (mask > 0).astype(np.uint8)

    # Perform a dilation operation to merge nearby green areas
    kernel = np.ones(dilation_kernel_size, np.uint8)  # Adjust the kernel size as needed
    dilated_mask = cv2.dilate(binary_mask, kernel, iterations=1)

    # Find contours in the dilated mask
    contours, _ = cv2.findContours(dilated_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Initialize a list to store the bounding rectangles of high-density regions
    bounding_rectangles = []

    # Find bounding rectangles for all high-density regions
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 1000:
            x, y, w, h = cv2.boundingRect(contour)
            bounding_rectangles.append((x, y, w, h))

    # Initialize a list to store the sum of pixel values for each rectangle
    sum_pixel_values = []

    # Calculate sum of pixel values for each rectangle and store it
    for x, y, w, h in bounding_rectangles:
        region = isolated_green[y:y+h, x:x+w]
        sum_pixels = np.sum(region)
        sum_pixel_values.append((x, y, w, h, sum_pixels))

    # Sort bounding rectangles by the sum of pixel values in descending order
    sum_pixel_values.sort(key=lambda rect: rect[4], reverse=True)

    # Update the rest of the code to use the sorted sum_pixel_values
    top_24_rectangles = [rect[:4] for rect in sum_pixel_values[:24]]

    # Calculate the maximum square size among the 24 regions
    max_square_size = max(max(w, h) for _, _, w, h in top_24_rectangles)

    # Initialize a list to store the labeled regions with center coordinates
    labeled_regions = []

    # Draw squares of the maximum size centered at the calculated centers
    for idx, (x, y, w, h) in enumerate(top_24_rectangles):
        center_x = x + w // 2
        center_y = y + h // 2
        
        # Calculate the coordinates for the square
        x1 = center_x - max_square_size // 2
        x2 = center_x + max_square_size // 2
        y1 = center_y - max_square_size // 2
        y2 = center_y + max_square_size // 2
        
        # Store the center along with the region
        labeled_regions.append(((center_y, center_x), idx + 1, isolated_green[y1:y2, x1:x2]))

    # Sort the regions by their center y-coordinate, then by their x-coordinate
    labeled_regions.sort(key=lambda x: (x[0][0]))

    # Group 4 by 4
    for i in range(0, len(labeled_regions), 4):
        labeled_regions[i:i+4] = sorted(labeled_regions[i:i+4], key=lambda x: x[0][1])

    # Change the index to match the order
    for i in range(len(labeled_regions)):
        labeled_regions[i] = (labeled_regions[i][0], i+1, labeled_regions[i][2])


    # Reconstruct each region tuple to include the surface area
    labeled_regions_with_area = []
    for region in labeled_regions:
        center, label, region_image = region
        non_zero_pixels = np.count_nonzero(region_image)*conversion_factor**2
        # 4 decimal places
        non_zero_pixels = round(non_zero_pixels, 4)
        labeled_regions_with_area.append((center, label, region_image, non_zero_pixels))

    # Plotting
    # Limit the number of regions
    labeled_regions_with_area = labeled_regions_with_area[:max_regions]

    # Update the labels within labeled_regions_with_area
    for i, (_, label, region, area) in enumerate(labeled_regions_with_area):
        new_label = label_mapping[label]
        labeled_regions_with_area[i] = ((_, new_label, region, area))

    # Plotting with 6 rows and 4 columns
    fig, axes = plt.subplots(grid_size, num_columns, figsize=(9,10))

    for idx, (_, label, region, area) in enumerate(labeled_regions_with_area):
        row = idx // num_columns  # Row index
        col = idx % num_columns   # Column index
        
        axes[row, col].imshow(region)
        axes[row, col].set_title(f'{label}\nArea: {area} cm²')
        axes[row, col].axis('off')

    # Make sure to handle any additional subplots if the number of regions is less than the grid size
    total_plots = grid_size * num_columns
    for idx in range(len(labeled_regions_with_area), total_plots):
        row = idx // num_columns
        col = idx % num_columns
        axes[row, col].axis('off')

    # Adjust layout
    plt.tight_layout()
    
    # Save the plot to a buffer with bbox_inches='tight' to include all content
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=90)
    plt.close()
    buf.seek(0)
    img = Image.open(buf)

    # Create a copy of the isolated green image to draw squares on
    squares_image = isolated_green.copy()

    # Iterate through labeled_regions_with_area and draw squares with labels
    for (center, label, region_image, _) in labeled_regions_with_area:
        center_y, center_x = center
        h, w, _ = region_image.shape

        # Calculate the coordinates for the square
        x1 = center_x - w // 2
        x2 = center_x + w // 2
        y1 = center_y - h // 2
        y2 = center_y + h // 2

        # Draw the square
        cv2.rectangle(squares_image, (x1, y1), (x2, y2), (255, 0, 0), 3)
        
        # Draw the label with a larger font size
        cv2.putText(squares_image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 0, 0), 3)

    # Convert the second plot (OpenCV image with squares and labels) to a PIL Image
    squares_image_rgb = cv2.cvtColor(squares_image, cv2.COLOR_BGR2RGB)  # Convert from BGR to RGB
    plot_img2 = Image.fromarray(squares_image_rgb)

    # Prepare text data
    text_data = '\n'.join([f'{label}: {area} cm²' for _, label, _, area in labeled_regions_with_area])

    return img, text_data, plot_img2



def resize_image_aspect_ratio(image, max_size):
    """
    Resizes the image while maintaining aspect ratio.
    Args:
        image: PIL Image object.
        max_size: Tuple (max_width, max_height) for the maximum allowed size.
    Returns:
        Resized PIL Image object.
    """
    original_width, original_height = image.size
    max_width, max_height = max_size
    scale = min(max_width/original_width, max_height/original_height)

    new_width = int(original_width * scale)
    new_height = int(original_height * scale)
    
    return image.resize((new_width, new_height), Image.BICUBIC)


