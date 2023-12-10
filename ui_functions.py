import tkinter as tk
from tkinter import ttk
from image_processing import process_image, resize_image_aspect_ratio
from tkinter import filedialog
from PIL import Image, ImageTk
from tkinter import simpledialog, messagebox    
import logging
from utils import compute_conversion_factor, export_to_csv
from config import choose_label

# Global variables for slider values
global lower_green_sliders, upper_green_sliders, min_area_slider, dilation_kernel_size_slider, max_regions_slider, grid_size_slider, num_columns_slider

# Function to create a labeled slider with a default value
def create_slider(parent, label, from_, to, default, row, column, command=None):
    tk.Label(parent, text=label).grid(row=row, column=column)
    slider = tk.Scale(parent, from_=from_, to=to, orient=tk.HORIZONTAL, command=lambda value: command())
    slider.set(default)  # Set the default value
    slider.grid(row=row, column=column + 1)
    return slider

def update_color_preview(sliders, preview_label):
    r, g, b = [slider.get() for slider in sliders]
    preview_label.config(bg=f'#{r:02x}{g:02x}{b:02x}')

def create_color_sliders(parent, label, default_values, row):
    tk.Label(parent, text=label).grid(row=row, column=0)

    def slider_update_command():
        update_color_preview(color_sliders, color_preview)

    r_slider = create_slider(parent, "R", 0, 255, default_values[0], row, 1, command=slider_update_command)
    g_slider = create_slider(parent, "G", 0, 255, default_values[1], row + 1, 1, command=slider_update_command)
    b_slider = create_slider(parent, "B", 0, 255, default_values[2], row + 2, 1, command=slider_update_command)
    color_sliders = (r_slider, g_slider, b_slider)

    color_preview = tk.Label(parent, width=2, bg="#FFFFFF")
    color_preview.grid(row=row, column=3, rowspan=3)

    slider_update_command()  # Initial color preview update
    return color_sliders


def setup_ui(root):
    logging.debug('This message will be logged.')
    logging.basicConfig(filename='app.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s')

    # Declare sliders as global
    global lower_green_sliders, upper_green_sliders, min_area_slider, dilation_kernel_size_slider, max_regions_slider, grid_size_slider, num_columns_slider


    root.title("Plante")
    root.geometry("1200x800")  # Set default size

    # Initialize global variables
    original_img_path = None
    global label_preset_var
    label_preset_var = tk.IntVar(value=1)  # Default to preset 1

    # New frame for sliders and color selectors
    settings_frame = tk.LabelFrame(root, text="Settings")
    settings_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

    # Adjust the existing left and right frames
    left_frame = tk.Frame(root)
    right_frame = tk.Frame(root)

    # Pack the frames after creating all of them
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    notebook = ttk.Notebook(right_frame)
    notebook.pack(fill=tk.BOTH, expand=True)

    # Frame for buttons
    button_frame = tk.Frame(left_frame)
    button_frame.pack(pady=10, anchor='nw')

    preset_frame = tk.Frame(button_frame)  # Frame to hold the checkboxes
    preset_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    tk.Radiobutton(preset_frame, text="Label Preset 1", variable=label_preset_var, value=1).pack(side=tk.LEFT)
    tk.Radiobutton(preset_frame, text="Label Preset 2", variable=label_preset_var, value=2).pack(side=tk.LEFT)

    label_mapping = choose_label(label_preset_var.get())

    # Upload buttons
    upload_btn = tk.Button(button_frame, text="Upload Image", command=lambda: upload_and_draw_image(root))
    process_btn = tk.Button(button_frame, text="Process and Display Image", command=lambda: process_and_display_image(left_image_label, text_display, root, label_mapping, conversion_factor))

    upload_btn.pack(side=tk.LEFT, padx=5)
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


    # lower_green and upper_green color selectors with default values
    lower_green_sliders = create_color_sliders(settings_frame, "Lower Green", (35, 52, 72), 0)
    upper_green_sliders = create_color_sliders(settings_frame, "Upper Green", (102, 255, 255), 3)

    # Sliders for other parameters with default values
    min_area_slider = create_slider(settings_frame, "Min Area", 0, 5000, 1000, 6, 0)
    # Dilation kernel size slider
    dilation_kernel_size_slider = create_slider(settings_frame, "Dilation Kernel Size", 1, 100, 50, 7, 0)
    max_regions_slider = create_slider(settings_frame, "Max Regions", 1, 50, 24, 9, 0)
    grid_size_slider = create_slider(settings_frame, "Grid Size", 1, 20, 6, 10, 0)
    num_columns_slider = create_slider(settings_frame, "Number of Columns", 1, 10, 4, 11, 0)



    root.mainloop()

def upload_and_draw_image(root):
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
        canvas.bind("<Button-1>", lambda event: get_point(event, root))

def get_point(event,root):
    global points, canvas
    # Add point to the list
    points.append((event.x, event.y))

    # Draw the point on the canvas
    canvas.create_oval(event.x - 5, event.y - 5, event.x + 5, event.y + 5, fill='red')

    # If two points are drawn, ask for real-world distance
    if len(points) == 2:
        draw_segment_and_ask_distance(root)

def draw_segment_and_ask_distance(root):
    global points, canvas, scaling_factor, conversion_factor
    # Adjust points to original image scale
    adjusted_points = [(x / scaling_factor, y / scaling_factor) for x, y in points]

    # Compute pixel distance on original image scale
    pixel_distance = ((adjusted_points[1][0] - adjusted_points[0][0]) ** 2 + (adjusted_points[1][1] - adjusted_points[0][1]) ** 2) ** 0.5

    # Alert the pixel distance
    tk.messagebox.showinfo("Pixel Distance", f"The pixel distance between the points is: {pixel_distance:.2f}")

    # Ask for real-world distance
    distance = simpledialog.askfloat("Input", "Enter real-world distance for the segment (cm):", parent=root)

    if distance:
        conversion_factor = compute_conversion_factor(distance, pixel_distance)

def process_and_display_image(left_image_label, text_display, root, label_mapping, conversion_factor):
    global lower_green_sliders, upper_green_sliders, min_area_slider, dilation_kernel_size_slider, max_regions_slider, grid_size_slider, num_columns_slider
    
    # Retrieve values from sliders
    lower_green = (lower_green_sliders[0].get(), lower_green_sliders[1].get(), lower_green_sliders[2].get())
    upper_green = (upper_green_sliders[0].get(), upper_green_sliders[1].get(), upper_green_sliders[2].get())
    min_area = min_area_slider.get()
    dilation_kernel_size = (dilation_kernel_size_slider.get(), dilation_kernel_size_slider.get())
    max_regions = max_regions_slider.get()
    grid_size = grid_size_slider.get()
    num_columns = num_columns_slider.get()

    if original_img_path:
        # Process the image
        processed_img, text_data, verification_plot = process_image(original_img_path, conversion_factor, label_mapping, lower_green, upper_green, min_area, dilation_kernel_size, max_regions, grid_size, num_columns)

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