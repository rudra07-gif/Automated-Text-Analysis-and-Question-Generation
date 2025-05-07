This project is a comprehensive solution for automated text analysis and the generation of objective-type questions (MCQs) from input textual data. It is designed to aid educators, students, and developers working on intelligent learning systems by converting unstructured text into insightful assessments using natural language processing (NLP) techniques.

🔍 Features
Text Preprocessing: The system includes robust NLP preprocessing steps such as tokenization, stopword removal, lemmatization, and named entity recognition (NER), using spaCy and NLTK.

Key Concept Extraction: It automatically identifies important keywords, dates, places, and factual entities from the input paragraph using statistical and linguistic features.

Question Generation: Using rule-based templates and transformer models (e.g., T5 or BERT), the system generates grammatically correct and contextually relevant multiple-choice questions.

Distractor Generation: For each question, three plausible distractors (wrong options) are generated using WordNet, semantic similarity, or transformer-based masking to ensure quality and challenge.

Custom Input Support: Users can input any passage or topic, and the model dynamically creates MCQs suited for practice, testing, or revision.

Interactive Interface: The project includes a simple GUI (Tkinter or Flask-based) for uploading text and viewing generated questions with correct answers.

Evaluation Metrics: Optionally includes automated grading, precision, recall, and F1 score calculation if a labeled test set is provided.

💡 Use Cases
Intelligent tutoring systems

E-learning content generation

Corporate training assessment

Reading comprehension test creation

Cognitive ability evaluation

⚙️ Technologies Used
Python (3.8+)

spaCy, NLTK, Transformers (Hugging Face)

Flask or Tkinter for GUI

scikit-learn for evaluation metrics

📁 Project Structure
/data – Sample input files

/models – Pretrained models and scripts

/gui – Interface logic (Tkinter/Flask)

/utils – Helper functions

main.py – Execution entry point
