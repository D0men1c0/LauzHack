# VisionAI Assistant

**VisionAI Assistant** is a mobile application designed to analyze and interpret visual content using advanced artificial intelligence technologies. Users can upload images and video and interact with the system via natural language inputs, whether through text or voice commands. The application processes these inputs to provide comprehensive insights, including object detection, segmentation, and the extraction of specific attributes from images.

This project was developed during the **Lauz Hack** hackathon at EPFL in just **22 hours**, with a team of four people collaborating on distinct fields to parallelize the work. The roles were divided as follows:
- **NLP Specialist**: Focused on natural language query understanding and feature extraction.
- **Computer Vision Engineer**: Developed the segmentation pipeline and integrated it with the SAM model.
- **Frontend Developer**: Built the Flutter-based user interface to handle multi-modal input and display results.
- **Backend and Cloud Developer**: Deployed and hosted the system on **AWS EC2**, ensuring stable and scalable performance. Additionally, managed the Flask server to facilitate seamless communication between the models and the frontend.

Given the tight timeframe, this architecture demonstrates the team's efficiency in integrating state-of-the-art AI models into a functional and scalable system. However, there is significant potential for future improvements.

---

## Architecture Overview

The application architecture is composed of several key components:

### **Frontend**
- Built using **Flutter**, enabling cross-platform interface. 
- The frontend supports multiple modes of interaction, allowing users to provide inputs via:
  - Text
  - Voice recordings
  - Directly uploaded images (video support is planned for future improvements).

### **Backend**
- Developed with **Flask**, a lightweight Python-based web framework.
- Manages:
  - Communication between the user interface and the AI models.
  - Image processing and segmentation tasks.
  - Query analysis and result presentation.

### **Hosting**
- The Flask server and all AI models are deployed on an **AWS EC2 instance**, ensuring scalability and reliable performance.

### **Natural Language Understanding**
- We used **SBERT (Sentence-BERT)** to process the user's natural language query. SBERT identifies the main object or feature to analyze into complex input (e.g., "cars" in the query *"Hey, could you tell me how many red trucks with certain size are at the center of the image?"*).
- The similarity-based approach allows the system to match the query against predefined classes like "cars," "boats," "trees", or "people."

### **Computer Vision Model**
- Image segmentation is performed using **Meta's Segment Anything Model (SAM 2)**, which processes the image based on instructions derived from the user's query. 
- SAM is combined with **natural language prompts**, improving its capability to segment objects or regions of interest directly from the text input.  
  - GitHub Repo: [lang-segment-anything](https://github.com/luca-medeiros/lang-segment-anything)

### **Prompt Processing and Feature Extraction**
- After the **SAM model** segments the image, it outputs bounding boxes representing each detected segment. These bounding boxes, along with their coordinates, are stored in a dataset.  
- Our system computes and populates additional features for each segment (e.g., color, size, position) through feature engineering based on the raw segmentation data.  
- **ChatGPT (GPT-4o)** is then used to interpret the user's natural language prompt and execute code that filters the dataset to extract relevant results:
  - For example:
    - Query: *"How many red ships are in this picture?"*
    - Workflow:
      1. The precomputed dataset contains attributes for each segment (`Object: Boat`, `Color: Red`, `Size`, `Area`, `Coordinate`, etc.).
      2. GPT parses the user's query, identifies the relevant features (e.g., `Object: Boat`, `Color: Red`), and writes code to filter the dataset accordingly.
      3. The filtered dataset is analyzed to calculate the result (e.g., "4 red boats").
      4. The application visually highlights only the bounding boxes that match the query, overlaying them on the image.
- This process leverages GPT to execute automated filtering and analysis while ensuring precision through precomputed features in the dataset.

---

## Workflow in Detail

1. **User Input**
   - The user interacts with the app using natural language, either through text or voice. Example:
     > *"Hi, can you segment all the red cars in the center of this image that are around 3 meters in size?"*
   - If input is provided via voice, the **Whisper** speech-to-text model converts the recording into text.

2. **Query Understanding**
   - The text input is processed by **SBERT**, which matches the query to predefined categories or classes. For instance:
     - Query: *"red cars in the center"*
     - Identified class: *"Car"*

3. **Image Segmentation**
   - The **SAM 2 model** receives the image and the segmented class (e.g., *"cars"*).
   - SAM segments all objects of the identified class and outputs bounding boxes for each detected segment.

4. **Dataset Creation and Feature Engineering**
   - The bounding boxes from SAM are used to create a dataset, with each segment annotated with attributes such as:
     - **Color**: Detected through pixel-level analysis of the segment.
     - **Size**: Computed based on the dimensions of the bounding box.
     - **Position**: Derived from the coordinates of the bounding box within the image.
   - This dataset forms the foundation for all subsequent analysis.

5. **Query Refinement and Filtering**
   - The natural language query, along with the dataset, is passed to **ChatGPT (GPT-4o)**.  
     - GPT interprets the query and generates code to filter the dataset based on the requested features. For example:
       - Query: *"How many red trucks are in this image?"*
       - GPT writes and executes code to:
         1. Filter segments where `Object = Truck` and `Color = Red`.
         2. Count the filtered segments.
   - This automated process ensures the dataset is refined to match the user’s request.

6. **Output Presentation**
   - The filtered dataset is used to generate the final visual output.
   - Relevant segments are highlighted directly on the image (e.g., bounding boxes around red trucks).
   - The results (e.g., "4 red trucks") are displayed in the app’s user interface, along with the annotated image.

---


## Advantages of VisionAI Assistant

### **Enhanced Query Capabilities**
Unlike general-purpose multimodal models (e.g., ChatGPT with basic image input), VisionAI Assistant allows users to make complex queries about specific image features. Examples include:
- Counting objects of a specific type (e.g., *"How many blue cars are in the parking lot?"*).
- Filtering objects by attributes like size, position, or color.

### **Modular and Scalable Design**
By separating natural language processing, image segmentation, and feature extraction into distinct modules, the system is:
- Easier to maintain and upgrade.
- Scalable for more complex use cases, such as video analysis or real-time segmentation.

### **Custom Feature Engineering**
The use of an intermediate dataset for feature engineering allows for advanced queries. For example:
- *"Which cars are red, larger than 3 meters, and located on the left side of the image?"*
- Such queries are processed efficiently using our feature engineering pipeline.

---

## Limitations and Future Improvements

### **Current Limitations**
- **Video Processing**: Currently, only image processing is supported due to the computational limits of the hosting server. Video support requires a stronger virtual machine for faster inference.
- **Prompt Engineering**: While effective, further improvements in prompt refinement could enhance model accuracy and relevance.

### **Future Enhancements**
1. **Scalable Infrastructure**: Upgrading the hosting environment to handle high-throughput tasks like video processing.
2. **Expanded Feature Set**: Adding more attributes (e.g., material type, motion patterns for video) to the dataset for richer analysis.
3. **Interactive Query Refinement**: Allowing users to iteratively refine their queries based on intermediate results.

---

### **Conclusion**

VisionAI Assistant demonstrates the potential of integrating advanced AI models with intuitive interfaces to tackle complex visual analysis tasks efficiently. Despite being developed in only **22 hours**, the system achieves a high level of functionality and modularity. The collaborative effort of specialists in NLP, Computer Vision, Backend Development, and Cloud Engineering highlights the power of parallelized teamwork. While the project shows great promise, there are clear opportunities for enhancement, particularly in scalability and feature richness.
