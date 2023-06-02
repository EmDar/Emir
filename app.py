import os
import requests
from flask import Flask, render_template, request, abort, send_from_directory
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import io

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024  # 1 MB limit for uploaded files
UPLOAD_FOLDER = './uploads'  # папка для загруженных файлов
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
RECAPTCHA_SITE_KEY = '6Lc9_l4mAAAAAIXEKOigSV_PzRaWnzoySCfqP_0S'

def change_brightness(image, brightness, selected_channels):
    # Convert the image to numpy array
    img_array = np.array(image)

    # Apply brightness adjustment to the selected channels
    for channel in selected_channels:
        img_array[..., channel] += brightness

    # Limit the pixel values to the range of 0-255
    img_array = np.clip(img_array, 0, 255).astype(np.uint8)

    # Create and return the modified image
    modified_image = Image.fromarray(img_array)
    return modified_image


def get_color_distribution(img):
    colors = img.getcolors(img.size[0] * img.size[1])
    return sorted(colors, key=lambda x: x[0], reverse=True)[:10]

def plot_color_distribution(image, plot_filename):
    # Convert the image to numpy array
    img_array = np.array(image)

    # Calculate the color distribution for each channel separately
    color_dist_r, _ = np.histogram(img_array[..., 0].flatten(), bins=256, range=(0, 255))
    color_dist_g, _ = np.histogram(img_array[..., 1].flatten(), bins=256, range=(0, 255))
    color_dist_b, _ = np.histogram(img_array[..., 2].flatten(), bins=256, range=(0, 255))

    # Normalize the color distribution
    color_dist_normalized_r = color_dist_r / np.sum(color_dist_r)
    color_dist_normalized_g = color_dist_g / np.sum(color_dist_g)
    color_dist_normalized_b = color_dist_b / np.sum(color_dist_b)

    # Create the color distribution plot
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(color_dist_normalized_r, color='red', label='Red')
    ax.plot(color_dist_normalized_g, color='green', label='Green')
    ax.plot(color_dist_normalized_b, color='blue', label='Blue')

    # Set the plot title and labels
    ax.set_title('Color Distribution')
    ax.set_xlabel('Pixel Value')
    ax.set_ylabel('Normalized Frequency')

    # Add a legend
    ax.legend()

    # Save the plot to a file
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)

    with open(plot_filename, 'wb') as file:
        file.write(buf.getvalue())

@app.route('/brightness', methods=['POST'])
def brightness():
    # Get the uploaded file from the request
    file = request.files.get('file')

    # Check if a file was uploaded
    if not file:
        abort(400, 'No file was uploaded')

    # Check if the uploaded file is an image
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        abort(400, 'File is not an image')

    recaptcha_response = request.form.get('g-recaptcha-response')
    if not recaptcha_response:
        abort(400, 'reCAPTCHA verification failed')
    payload = {
        'secret': '6Lc9_l4mAAAAADkf6mAJyK6XERaHV6e5ubmcKQUn',
        'response': recaptcha_response
    }
    response = requests.post('https://www.google.com/recaptcha/api/siteverify', payload).json()
    if not response['success']:
        abort(400, 'reCAPTCHA verification failed')

    # Load the image
    img = Image.open(file)

    # Get the brightness level from the request
    brightness_level = int(request.form.get('brightness'))

    # Get the selected color channels from checkboxes
    selected_channels = []
    if request.form.get('red_checkbox'):
        selected_channels.append(0)  # Red channel
    if request.form.get('green_checkbox'):
        selected_channels.append(1)  # Green channel
    if request.form.get('blue_checkbox'):
        selected_channels.append(2)  # Blue channel

    # Change the brightness of the image for the selected channels
    modified_image = change_brightness(img, brightness_level, selected_channels)
    orig_image = img

    # Calculate color distributions of original and modified images
    orig_colors = get_color_distribution(img)
    modified_colors = get_color_distribution(modified_image)

    # Save the modified image to a file
    orig_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'rig.png')
    orig_image.save(orig_filename)

    modified_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'modified.png')
    modified_image.save(modified_filename)

    # Create the color distribution plot for the original image
    plot_orig_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'plot_orig.png')
    plot_color_distribution(img, plot_orig_filename)

    # Create the color distribution plot for the modified image
    plot_modified_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'plot_modified.png')
    plot_color_distribution(modified_image, plot_modified_filename)

    # Render the result page
    return render_template('result.html', orig_colors=orig_colors, modified_colors=modified_colors, orig_image=orig_filename,
                           modified_image=modified_filename, plot_orig=plot_orig_filename,
                           plot_modified=plot_modified_filename)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', sitekey=RECAPTCHA_SITE_KEY)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.config['UPLOAD_FOLDER'] = 'uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
