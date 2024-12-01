import base64
import io
import os
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
import cv2
from PIL import Image, ImageDraw
from lang_sam import LangSAM
import pickle
import textwrap

load_dotenv()
sentence_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
options = os.getenv("OPTIONS").split(",")
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def output_to_text(query, output):
    if isinstance(output, pd.DataFrame):
        output_string = output.to_string()
    else:
        output_string = str(output)

    messages = [
    {"role": "system", "content": f"The user asked: '{query}'. The following is the result:\n\nOutput:\n{output_string}\n\nProvide a concise and general explanation of the result in simple terms:"}
    ]


    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=1000,
        temperature=0,
    )

    return response.choices[0].message.content

def parse_coordinates(coord):
    if isinstance(coord, str):
        return list(map(float, coord.strip("[]").split()))
    elif isinstance(coord, np.ndarray):
        return coord.tolist()
    else:
        raise ValueError("Unsupported type for coordinates.")


def main_predict(image_path, query):

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

    '''
    plt.figure(figsize=(10, 10))
    plt.imshow(image_pil)
    plt.axis('off')

    for result in results:
        for i, box in enumerate(result["boxes"]):
            x_min, y_min, x_max, y_max = box
            area = (x_max - x_min) * (y_max - y_min) / image_area
            if area > 0.8:
                continue
            plt.gca().add_patch(plt.Rectangle(
                (x_min, y_min), x_max - x_min, y_max - y_min,
                edgecolor='red', facecolor='none', linewidth=2
            ))

    plt.title("Segmentation on Original Image")
    plt.show()'''

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
            "color": color_category,
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
            The dataframe contains the following columns: {df.columns}. Image dimensions are {image_width}x{image_height}, and the total area is {image_area}. 
            The user's query is: "{query}".

            - If the query explicitly mentions a color filter:
                - Use the `color_category` column to filter rows where the `color_category` matches the specified color name.
                - For RGB ranges, filter rows where `mean_color_R`, `mean_color_G`, and `mean_color_B` fall within the specified range. If no range is provided, apply a default tolerance of {tolerance} per channel.

            Write Python code based on the query and assign the results as follows:
            - `filtered_data`: A pandas DataFrame containing rows that match the filtering criteria without any aggregation.
            - `output_variable`: The aggregated result if the query requires aggregation.

            Do not include comments, import statements, or library declarations. Write only the Python code.
        """}
    ]

    filtered_data = None
    try:
        filter_code = get_filter_code(prompt=messages).replace("```python", "").replace("```", "").strip()
        print(filter_code)
        exec(
            filter_code +
            textwrap.dedent(
                """
                with open('filtered_data.pkl', 'wb') as f:
                    pickle.dump(filtered_data, f)
                
                with open('output_variable.pkl', 'wb') as f:
                    pickle.dump(output_variable, f)
                """
            )
        )

        with open("filtered_data.pkl", "rb") as f:
            filtered_data = pickle.load(f)

        
        with open("output_variable.pkl", "rb") as f:
            output_variable = pickle.load(f)

        print(output_variable)
        print(type(output_variable))

        try:
            original_image = Image.open(image_path)

            highlighted_image = original_image.copy()
            draw = ImageDraw.Draw(highlighted_image)

            rectangles_image = Image.new("RGB", original_image.size, (0, 0, 0))

            for _, row in filtered_data.iterrows():
                rect_coords = [
                    list(map(float, parse_coordinates(row["coord_1"]))),
                    list(map(float, parse_coordinates(row["coord_2"]))),
                    list(map(float, parse_coordinates(row["coord_3"]))),
                    list(map(float, parse_coordinates(row["coord_4"])))
                ]

                rect_coords = [tuple(map(int, coord)) for coord in rect_coords]

                draw.polygon(rect_coords, outline="red", width=2)

                x1, y1 = rect_coords[0]
                x3, y3 = rect_coords[2]
                cropped_rectangle = original_image.crop((x1, y1, x3, y3))

                rectangles_image.paste(cropped_rectangle, (x1, y1))

        except Exception as e:
            print(f"An error occurred while visualizing the results: {e}")
            return None, None

        buffered = io.BytesIO()
        highlighted_image.save(buffered, format="PNG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        return output_to_text(query, str(output_variable)), image_base64
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None

if __name__ == "__main__":
    image_path = "ships.jpg"
    query = "Return the gray ships in the space."
    uno, due = main_predict(image_path, query)