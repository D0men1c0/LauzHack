from PIL import Image
from lang_sam import LangSAM
from matplotlib import pyplot as plt
import numpy as np
model = LangSAM()
image_pil = Image.open("./assets/parking2.jpg").convert("RGB")
text_prompt = "car."

# Fai partire un timer per misurare il tempo di esecuzione
import time
start_time = time.time()

results = model.predict([image_pil], [text_prompt], box_threshold=0.23)

# Calcola il tempo di esecuzione
end_time = time.time()
execution_time = end_time - start_time
print(f"Tempo di esecuzione: {execution_time} secondi")

try:
    # Visualizza l'immagine
    plt.figure(figsize=(10, 10))
    plt.imshow(image_pil)
    plt.axis('off')

    # Sovrapponi le predizioni
    for result in results:
        # Disegna le bounding box
        for box in result["boxes"]:
            x_min, y_min, x_max, y_max = box
            plt.gca().add_patch(plt.Rectangle(
                (x_min, y_min), x_max - x_min, y_max - y_min,
                edgecolor='red', facecolor='none', linewidth=2, label="Box"
            ))

        # Sovrapponi le maschere
        mask = result["masks"][0]
        plt.imshow(mask, cmap='jet', alpha=0.5)  # Sovrapposizione della maschera con trasparenza

    # Printa e salva i risultati in un numpyarray
    #print(results)
    # Salva i risultati in un numpy array npz
    np.savez("results.npz", results=results)
    

    plt.title("Immagine con Predizioni")
    plt.show()

except FileNotFoundError:
    print("File immagine non trovato. Controlla il percorso.")