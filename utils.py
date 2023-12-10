import csv
from tkinter import filedialog

# Utility functions
def compute_conversion_factor(real_distance, pixel_distance):
    global points, conversion_factor

    # Compute conversion factor (real / pixel)
    conversion_factor = real_distance / pixel_distance
    print("Conversion Factor:", conversion_factor)
    return conversion_factor

def export_to_csv(text_data):
    # Export the text data to a CSV file
    file_path = filedialog.asksaveasfilename(defaultextension='.csv')
    if file_path:
        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            for line in text_data.split('\n'):
                writer.writerow([line])
