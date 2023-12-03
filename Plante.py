import tkinter as tk
from tkinter import ttk, filedialog, simpledialog
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np
from matplotlib import pyplot as plt
import io
import csv
import logging

logging.debug('This message will be logged.')
logging.basicConfig(filename='app.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s')


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


def upload_and_draw_image():
    global original_img_path, canvas, points, scaling_factor
    file_path = filedialog.askopenfilename()
    if file_path:
        original_img_path = file_path
        original_img = Image.open(file_path)

        # Set maximum size for the drawing window
        max_window_size = (800, 600)  # width, height

        # Calculate the scaling factor
        scaling_factor = min(max_window_size[0] / original_img.width, max_window_size[1] / original_img.height)

        # Resize the image to fit the window if it's too large
        if original_img.width > max_window_size[0] or original_img.height > max_window_size[1]:
            original_img.thumbnail(max_window_size)

        img = ImageTk.PhotoImage(original_img)

        # Create a new window for drawing
        draw_window = tk.Toplevel(root)
        draw_window.title("Draw Segment for Scale Calibration")

        # Create a canvas for drawing and display the image
        canvas = tk.Canvas(draw_window, width=img.width(), height=img.height())
        canvas.pack()
        canvas.create_image(0, 0, anchor='nw', image=img)
        canvas.image = img  # Keep a reference

        # Initialize points list
        points = []

        # Bind mouse click event
        canvas.bind("<Button-1>", get_point)


def get_point(event):
    global points, canvas
    # Add point to the list
    points.append((event.x, event.y))

    # Draw the point on the canvas
    canvas.create_oval(event.x - 5, event.y - 5, event.x + 5, event.y + 5, fill='red')

    # If two points are drawn, ask for real-world distance
    if len(points) == 2:
        draw_segment_and_ask_distance()

def draw_segment_and_ask_distance():
    global points, canvas, scaling_factor
    # Adjust points to original image scale
    adjusted_points = [(x / scaling_factor, y / scaling_factor) for x, y in points]

    # Compute pixel distance on original image scale
    pixel_distance = ((adjusted_points[1][0] - adjusted_points[0][0]) ** 2 + (adjusted_points[1][1] - adjusted_points[0][1]) ** 2) ** 0.5

    # Alert the pixel distance
    tk.messagebox.showinfo("Pixel Distance", f"The pixel distance between the points is: {pixel_distance:.2f}")

    # Ask for real-world distance
    distance = simpledialog.askfloat("Input", "Enter real-world distance for the segment (cm):", parent=root)

    if distance:
        compute_conversion_factor(distance, pixel_distance)

def compute_conversion_factor(real_distance, pixel_distance):
    global points, conversion_factor

    # Compute conversion factor (real / pixel)
    conversion_factor = real_distance / pixel_distance
    print("Conversion Factor:", conversion_factor)
    # You can now use this conversion factor in your area computation

def export_to_csv(text_data):
    # Export the text data to a CSV file
    file_path = filedialog.asksaveasfilename(defaultextension='.csv')
    if file_path:
        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            for line in text_data.split('\n'):
                writer.writerow([line])

def upload_image():
    global original_img_path
    file_path = filedialog.askopenfilename()
    if file_path:
        original_img_path = file_path
        original_img = Image.open(file_path)
        original_img.thumbnail((left_frame.winfo_width(), left_frame.winfo_height()))
        img = ImageTk.PhotoImage(original_img)
        left_image_label.config(image=img)
        left_image_label.image = img

def process_and_display_image():
    if original_img_path:
        # Process the image
        processed_img, text_data, verification_plot = process_image(original_img_path)

        # Set maximum size for the display window
        max_display_size = (800, 600)  # width, height
        max_display_size2 = (1000, 700)  # width, height

        # Resize the processed image to fit the window if it's too large
        processed_img = resize_image_aspect_ratio(processed_img, max_display_size2)

        # Convert the processed image for Tkinter
        img = ImageTk.PhotoImage(processed_img)

        # Create the new window
        new_window = tk.Toplevel(root)
        new_window.title("Processed Image")

        # Set the size of the new window to match the image size
        new_window.geometry(f'{img.width()}x{img.height()}')

        # Display processed image in the new window
        processed_img_label = tk.Label(new_window, image=img)
        processed_img_label.pack()

        # Keep a reference to the image to prevent garbage collection
        processed_img_label.image = img

        # Resize the verification plot to fit the window if it's too large
        verification_plot = resize_image_aspect_ratio(verification_plot, max_display_size)

        # Convert the verification plot for Tkinter
        verification_plot_tk = ImageTk.PhotoImage(verification_plot)

        # Display plot image in the left frame
        left_image_label.config(image=verification_plot_tk)
        left_image_label.image = verification_plot_tk  # Keep a reference

        # Display text data in a tab in the right frame of the main window
        text_display.delete('1.0', tk.END)  # Clear previous text
        text_display.insert(tk.END, text_data)



def process_image(image_path):

    # Load the image
    file_path = image_path
    image = cv2.imread(file_path)

    # Convert to RGB for matplotlib compatibility and HSV for color segmentation
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Define the range of green color in HSV
    lower_green = np.array([35, 52, 72])
    upper_green = np.array([102, 255, 255])

    # Threshold the HSV image to get only green colors
    mask = cv2.inRange(image_hsv, lower_green, upper_green)

    # Bitwise-AND mask and original image to isolate the green area
    isolated_green = cv2.bitwise_and(image_rgb, image_rgb, mask=mask)

    # Convert the mask to binary
    binary_mask = (mask > 0).astype(np.uint8)

    # Perform a dilation operation to merge nearby green areas
    kernel = np.ones((50, 50), np.uint8)  # Adjust the kernel size as needed
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
    # Limit the number of regions to 24 (3 columns * 8 rows)
    max_regions = 24
    labeled_regions_with_area = labeled_regions_with_area[:max_regions]


    # Define a dictionary to map original labels to new labels
    label_mapping = {
        1: "U1",
        2: "U6",
        3: "U5",
        4: "R1",
        5: "U10",
        6: "G3",
        7: "R7",
        8: "R3",
        9: "G4",
        10: "U7",
        11: "U3",
        12: "R5",
        13: "U4",
        14: "R4",
        15: "G2",
        16: "U9",
        17: "R8",
        18: "U8",
        19: "R10",
        20: "R9",
        21: "G1",
        22: "R6",
        23: "R2",
        24: "U2"
    }

    # Update the labels within labeled_regions_with_area
    for i, (_, label, region, area) in enumerate(labeled_regions_with_area):
        new_label = label_mapping[label]
        labeled_regions_with_area[i] = ((_, new_label, region, area))

    # Plotting with 6 rows and 4 columns
    grid_size = 6  # 6 rows
    num_columns = 4  # 4 columns
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

    # Display the image with squares and labels
    # plt.imshow(squares_image)
    # plt.title('Plants with corresponding labels')
    # plt.axis('off')
    # plt.show()

    # Prepare text data
    text_data = '\n'.join([f'{label}: {area} cm²' for _, label, _, area in labeled_regions_with_area])

    return img, text_data, plot_img2

# Create the main window
root = tk.Tk()
root.title("Plante")
root.geometry("1200x800")  # Set default size

# Initialize global variables
original_img_path = None

# Create frames
left_frame = tk.Frame(root)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

right_frame = tk.Frame(root)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

notebook = ttk.Notebook(right_frame)
notebook.pack(fill=tk.BOTH, expand=True)

# Frame for buttons
button_frame = tk.Frame(left_frame)
button_frame.pack(pady=10, anchor='nw')

# Upload button
# upload_btn = tk.Button(button_frame, text="Upload Image", command=upload_image)
upload_btn = tk.Button(button_frame, text="Upload Image", command=upload_and_draw_image)
upload_btn.pack(side=tk.LEFT, padx=5)

# Process and display button
process_btn = tk.Button(button_frame, text="Process and Display Image", command=process_and_display_image)
process_btn.pack(side=tk.LEFT, padx=5)

# Image label for left_frame (Original Image)
left_image_label = tk.Label(left_frame)
left_image_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

right_image_label = tk.Label(right_frame)
right_image_label.pack(fill=tk.BOTH, expand=True)

# Create a tab for displaying text
text_tab = tk.Frame(notebook)
notebook.add(text_tab, text='Data')

# Text widget for displaying data
text_display = tk.Text(text_tab, wrap=tk.WORD)
text_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Export button
export_button = tk.Button(button_frame, text="Export to CSV", command=lambda: export_to_csv(text_display.get('1.0', tk.END)))
export_button.pack(side=tk.LEFT, padx=5)


root.mainloop()
