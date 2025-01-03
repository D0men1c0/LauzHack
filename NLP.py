import os
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
import cv2
from PIL import Image, ImageDraw
from lang_sam import LangSAM
from matplotlib import pyplot as plt

query = "Select the gray ships in the space."
image_path = "ships.jpg"

def main_predict(image_path, query):

    load_dotenv()
    sentence_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
    options = os.getenv("OPTIONS").split(",")
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    features = os.getenv("FEATURES").split(",")

    image = cv2.imread(image_path)

    image_height, image_width, _ = image.shape
    image_area = image_width * image_height

    sentence_embedding = sentence_model.encode([query])[0]
    options_embeddings = sentence_model.encode(options)

    similarities = {}
    for i, option in enumerate(options):
        similarity = np.dot(sentence_embedding, options_embeddings[i]) / (np.linalg.norm(sentence_embedding) * np.linalg.norm(options_embeddings[i]))
        similarities[option] = similarity

    best_option = max(similarities, key=similarities.get)

    print(f"Most Probability world is '{best_option}' with similarity {similarities[best_option]:.4f}")

    def get_filter_code(prompt: str) -> str:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=prompt,
            max_tokens=1000,
            temperature=0,
        )
        
        return response.choices[0].message.content


    model_sam = LangSAM()
    image_pil = Image.open(image_path).convert("RGB")
    results = model_sam.predict([image_pil], [f"{best_option}."], box_threshold=0.23)


    plt.figure(figsize=(10, 10))
    plt.imshow(image_pil)
    plt.axis('off')

    # Sovrapposizione dei riquadri direttamente sull'immagine originale
    for result in results:
        for i, box in enumerate(result["boxes"]):
            x_min, y_min, x_max, y_max = box
            area = (x_max - x_min) * (y_max - y_min) / image_area
            if area > 0.8:
                # Ignora riquadri troppo grandi
                continue
            # Disegna il rettangolo direttamente sull'immagine originale
            plt.gca().add_patch(plt.Rectangle(
                (x_min, y_min), x_max - x_min, y_max - y_min,
                edgecolor='red', facecolor='none', linewidth=2
            ))

    plt.title("Segmentation on Original Image")
    plt.show()

    def calculate_features(points, image):
        x_min = int(min(p[0] for p in points))
        x_max = int(max(p[0] for p in points))
        y_min = int(min(p[1] for p in points))
        y_max = int(max(p[1] for p in points))

        area = (x_max - x_min) * (y_max - y_min)
        image_area = image.shape[0] * image.shape[1]
        relative_area = area / image_area
        relative_height = (y_max - y_min) / image.shape[0]
        relative_width = (x_max - x_min) / image.shape[1]

        mean_x = np.mean([p[0] for p in points])
        mean_y = np.mean([p[1] for p in points])

        cropped_area = image[y_min:y_max, x_min:x_max]

        cropped_hsv = cv2.cvtColor(cropped_area, cv2.COLOR_BGR2HSV)

        color_ranges = {
            'black':  {'lower': np.array([0, 0, 0]),      'upper': np.array([180, 255, 50])},
            'white':  {'lower': np.array([0, 0, 200]),    'upper': np.array([180, 30, 255])},
            'gray':   {'lower': np.array([0, 0, 51]),     'upper': np.array([180, 50, 199])},
            'red1':   {'lower': np.array([0, 50, 50]),    'upper': np.array([10, 255, 255])},
            'red2':   {'lower': np.array([160, 50, 50]),  'upper': np.array([180, 255, 255])},
            'orange': {'lower': np.array([11, 50, 50]),   'upper': np.array([25, 255, 255])},
            'yellow': {'lower': np.array([26, 50, 50]),   'upper': np.array([34, 255, 255])},
            'green':  {'lower': np.array([35, 50, 50]),   'upper': np.array([85, 255, 255])},
            'blue':   {'lower': np.array([100, 150, 50]), 'upper': np.array([115, 255, 200])},
            'purple': {'lower': np.array([126, 50, 50]),  'upper': np.array([159, 255, 255])}
        }

        color_counts = {color: 0 for color in color_ranges.keys()}
        total_pixels = cropped_hsv.shape[0] * cropped_hsv.shape[1]

        for color, bounds in color_ranges.items():
            mask = cv2.inRange(cropped_hsv, bounds['lower'], bounds['upper'])

            if color == 'blue':
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

                height = mask.shape[0]
                reflection_region = int(height * 0.2)
                spatial_mask = np.zeros_like(mask)
                spatial_mask[reflection_region:, :] = 255
                mask = cv2.bitwise_and(mask, mask, mask=spatial_mask)

            count = cv2.countNonZero(mask)
            color_counts[color] += count

        red_count = color_counts['red1'] + color_counts['red2']
        color_counts['red'] = red_count
        del color_counts['red1']
        del color_counts['red2']

        total_color_pixels = sum(color_counts.values()) - color_counts.get('black', 0) - color_counts.get('white', 0)

        blue_ratio = color_counts['blue'] / total_color_pixels if total_color_pixels > 0 else 0

        if blue_ratio < 0.2:
            color_counts['blue'] = 0

        dominant_color = max(color_counts, key=color_counts.get)
        dominant_count = color_counts[dominant_color]
        dominant_percentage = (dominant_count / total_pixels) * 100

        min_threshold = 10

        if dominant_percentage < min_threshold:
            color_category = 'other'
        else:
            color_category = dominant_color

        return {
            "coord_1": points[0],
            "coord_2": points[1],
            "coord_3": points[2],
            "coord_4": points[3],
            "mean_x": mean_x,
            "mean_y": mean_y,
            "color_category": color_category,
            "area": area,
            "relative_area": relative_area,
            "relative_height": relative_height,
            "relative_width": relative_width
        }


    points_array = np.array([
        [
            [row[0], row[1]],
            [row[2], row[1]],
            [row[2], row[3]],
            [row[0], row[3]]
        ]
        for row in results[0]['boxes']
    ])

    dataset = []
    for points in points_array:
        features_dict = calculate_features(points, image)
        dataset.append(features_dict)

    df = pd.DataFrame(dataset)

    tolerance = 10

    messages = [
        {"role": "system", "content": "You are an assistant that helps write Python code."},
        {"role": "user", "content": 
        f"""
            Considering the following {df.columns} columns in pandas dataframes. Image dimensions are {image_width}x{image_height} and the area is {image_area}.
            The user's query is: "{query}".

            If the query includes a color filter:
            - If a specific color name is provided, use the color_category column to filter rows where the color_category matches the requested color.
            - If an RGB range is provided, filter rows where the mean_color_R, mean_color_G, and mean_color_B columns fall within the specified range or infer a default tolerance of {tolerance} per channel if not provided.

            Write the Python code based on the query and assign to a variable called filtered_data. Notice that you have to aggregate in some cases. 
            Do not include comments or import statements or library, only the Python code.
            """}
    ]
    filtered_data = None
    try:
        filter_code = get_filter_code(prompt=messages).replace("```python", "").replace("```", "").strip()
        print(filter_code)
        exec(filter_code + " \nfiltered_data.to_csv('filtered_data.csv', index=False)")

        filtered_data = pd.read_csv("filtered_data.csv")
        print(filtered_data)
        if len(filtered_data) == 0:
            print("No data found.")
        else:
            original_image = Image.open("ships.jpg")

            highlighted_image = original_image.copy()
            draw = ImageDraw.Draw(highlighted_image)

            rectangles_image = Image.new("RGB", original_image.size, (0, 0, 0))

            for _, row in filtered_data.iterrows():
                # Converte le coordinate da stringa a lista di numeri
                rect_coords = [
                    list(map(float, row["coord_1"].strip("[]").split())),
                    list(map(float, row["coord_2"].strip("[]").split())),
                    list(map(float, row["coord_3"].strip("[]").split())),
                    list(map(float, row["coord_4"].strip("[]").split()))
                ]

                rect_coords = [tuple(map(int, coord)) for coord in rect_coords]

                draw.polygon(rect_coords, outline="red", width=2)

                x1, y1 = rect_coords[0]
                x3, y3 = rect_coords[2]
                cropped_rectangle = original_image.crop((x1, y1, x3, y3))

                rectangles_image.paste(cropped_rectangle, (x1, y1))

            plt.figure(figsize=(12, 6))

            plt.subplot(1, 2, 1)
            plt.imshow(highlighted_image)
            plt.title("Original Image with Highlighted Rectangles")
            plt.axis("off")

            plt.subplot(1, 2, 2)
            plt.imshow(rectangles_image)
            plt.title("Image with Rectangles Only")
            plt.axis("off")

            plt.tight_layout()
            plt.show()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main_predict(image_path, query)