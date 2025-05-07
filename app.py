from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bootstrap import Bootstrap
import requests
import random
import nltk
import re
import mysql.connector
from mysql.connector import Error
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords, wordnet as wn
from nltk import pos_tag

# Initialize NLTK
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your-secret-key-123'  # Change this in production
bootstrap = Bootstrap(app)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Rudra@123',
    'database': 'quiz_app_db'
}


class Database:
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
        except Error as e:
            flash(f"Database connection failed: {str(e)}", "danger")
            raise

    def execute_query(self, query, params=None):
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            self.connection.commit()
            return cursor
        except Error as e:
            self.connection.rollback()
            flash(f"Database error: {str(e)}", "danger")
            raise

    def fetch_one(self, query, params=None):
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            return cursor.fetchone()
        except Error as e:
            flash(f"Database error: {str(e)}", "danger")
            raise

    def fetch_all(self, query, params=None):
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except Error as e:
            flash(f"Database error: {str(e)}", "danger")
            raise

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()


class ObjectiveTest:
    def __init__(self, data, no_of_ques):
        self.summary = data
        self.no_of_ques = no_of_ques

    def generate_test(self):
        trivial_pairs = self.get_trivial_sentences()
        random.shuffle(trivial_pairs)
        mcq_questions = []

        for item in trivial_pairs[:self.no_of_ques]:
            distractors = item["Similar"][:3]
            remaining = 3 - len(distractors)

            if remaining > 0:
                new_distractors = self.generate_random_distractors(
                    item["Answer"], item["POS"], remaining
                )
                new_distractors = [
                    d for d in new_distractors
                    if d.lower() != item["Answer"].lower()
                       and d not in distractors
                ]
                distractors += new_distractors[:remaining]

            distractors = list(set(distractors))[:3]
            options = distractors + [item["Answer"]]
            random.shuffle(options)

            mcq_questions.append({
                "Question": item["Question"],
                "Options": options,
                "Answer": item["Answer"]
            })
        return mcq_questions

    def get_trivial_sentences(self):
        sentences = sent_tokenize(self.summary)
        trivial_pairs = []
        for sent in sentences:
            trivial_pairs.extend(self.identify_trivial_words(sent))
        return trivial_pairs

    def identify_trivial_words(self, sentence):
        tokens = word_tokenize(sentence)
        tagged = pos_tag(tokens)
        patterns = [
            ('NN', 'NOUN'),
            ('VB', 'VERB'),
            ('JJ', 'ADJECTIVE'),
            ('RB', 'ADVERB'),
            ('PRP', 'PRONOUN')
        ]
        pairs = []

        for tag_prefix, pos_label in patterns:
            chunker = nltk.RegexpParser(f'CHUNK: {{<{tag_prefix}.*>}}')
            tree = chunker.parse(tagged)

            for subtree in tree.subtrees():
                if subtree.label() == 'CHUNK':
                    word, tag = subtree.leaves()[0]
                    pattern = re.compile(r'\b' + re.escape(word) + r'\b')
                    blank_sentence = pattern.sub('______', sentence, 1)
                    synonyms = self.get_synonyms(word, pos_label)

                    pairs.append({
                        "Answer": word,
                        "Question": blank_sentence,
                        "POS": pos_label,
                        "Similar": synonyms
                    })
        return pairs

    def get_synonyms(self, word, pos_label):
        pos_map = {
            'NOUN': 'n',
            'VERB': 'v',
            'ADJECTIVE': 'a',
            'ADVERB': 'r',
            'PRONOUN': None
        }
        wn_pos = pos_map.get(pos_label)
        synonyms = set()

        if wn_pos:
            for syn in wn.synsets(word, pos=wn_pos):
                for lemma in syn.lemmas():
                    synonym = lemma.name().replace('_', ' ').lower()
                    if synonym != word.lower():
                        synonyms.add(synonym.capitalize())
        return list(synonyms)[:5]

    def generate_random_distractors(self, correct_answer, pos_label, count=3):
        pos_tags = {
            'NOUN': ['NN', 'NNS', 'NNP', 'NNPS'],
            'VERB': ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'],
            'ADJECTIVE': ['JJ', 'JJR', 'JJS'],
            'ADVERB': ['RB', 'RBR', 'RBS'],
            'PRONOUN': ['PRP', 'PRP$']
        }.get(pos_label, [])

        words = word_tokenize(self.summary)
        tagged = pos_tag(words)
        candidates = [
            word for word, tag in tagged
            if tag in pos_tags and word.lower() != correct_answer.lower()
        ]
        candidates = list(set(candidates))
        random.shuffle(candidates)

        distractors = [c.capitalize() for c in candidates[:count]]

        if len(distractors) < count:
            other_words = [
                word for word, tag in tagged
                if word.lower() != correct_answer.lower()
                   and word not in candidates
            ]
            distractors += [w.capitalize() for w in other_words[:count - len(distractors)]]

        return distractors[:count]


@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash("Please enter both username and password", "danger")
            return render_template('login.html')

        db = Database()
        try:
            user = db.fetch_one(
                "SELECT * FROM users WHERE username = %s AND password = %s",
                (username, password)
            )
            if user:
                session['username'] = username
                return redirect(url_for('welcome'))
            else:
                flash("Invalid username or password", "danger")
        except Exception as e:
            flash(f"Login error: {str(e)}", "danger")

        return render_template('login.html')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not password or not confirm_password:
            flash("Please fill in all fields", "danger")
            return render_template('register.html')

        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return render_template('register.html')

        db = Database()
        try:
            # Check if username already exists
            existing_user = db.fetch_one(
                "SELECT * FROM users WHERE username = %s",
                (username,)
            )
            if existing_user:
                flash("Username already taken", "danger")
                return render_template('register.html')

            # Create new user
            db.execute_query(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, password)
            )
            flash("Registration successful! Please login", "success")
            return redirect(url_for('login'))
        except Error as e:
            flash(f"Registration failed: {str(e)}", "danger")
            return render_template('register.html')

    return render_template('register.html')


@app.route('/welcome')
def welcome():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('welcome.html', username=session['username'])


@app.route('/topic-quiz', methods=['GET', 'POST'])
def topic_quiz():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Fetch categories
    categories = []
    try:
        response = requests.get("https://opentdb.com/api_category.php")
        categories = response.json()["trivia_categories"]
    except Exception as e:
        flash(f"Failed to load categories: {str(e)}", "danger")

    if request.method == 'POST':
        session['topic_id'] = request.form.get('category')
        session['num_questions'] = int(request.form.get('num_questions', 5))
        return redirect(url_for('start_topic_quiz'))

    return render_template('topic_quiz_setup.html', categories=categories)


@app.route('/start-topic-quiz')
def start_topic_quiz():
    try:
        response = requests.get(
            f"https://opentdb.com/api.php?amount={session.get('num_questions', 5)}&category={session.get('topic_id')}&type=multiple"
        )
        questions = response.json()["results"]
        session['questions'] = questions
        session['current_question'] = 0
        session['score'] = 0
        return redirect(url_for('show_question'))
    except Exception as e:
        flash(f"Failed to load questions: {str(e)}", "danger")
        return redirect(url_for('topic_quiz'))


@app.route('/question')
def show_question():
    if 'current_question' not in session:
        return redirect(url_for('topic_quiz'))

    question = session['questions'][session['current_question']]
    options = question['incorrect_answers'] + [question['correct_answer']]
    random.shuffle(options)

    return render_template(
        'question.html',
        question=question['question'],
        options=options,
        question_num=session['current_question'] + 1,
        total_questions=len(session['questions'])
    )


@app.route('/submit-answer', methods=['POST'])
def submit_answer():
    selected_answer = request.form.get('answer')
    correct_answer = session['questions'][session['current_question']]['correct_answer']

    if selected_answer == correct_answer:
        session['score'] += 1

    if session['current_question'] < len(session['questions']) - 1:
        session['current_question'] += 1
        return redirect(url_for('show_question'))
    else:
        return redirect(url_for('show_results'))


@app.route('/results')
def show_results():
    db = Database()
    try:
        db.execute_query(
            "INSERT INTO quiz_results (user_name, topic_name, right_answers, wrong_answers) "
            "VALUES (%s, %s, %s, %s)",
            (session['username'], "General",
             session['score'], len(session['questions']) - session['score'])
        )
    except Error as e:
        flash(f"Failed to save results: {str(e)}", "danger")

    return render_template(
        'results.html',
        score=session['score'],
        total=len(session['questions']),
        questions=session['questions']
    )


@app.route('/paragraph-quiz', methods=['GET', 'POST'])
def paragraph_quiz():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        paragraph = request.form.get('paragraph')
        num_questions = int(request.form.get('num_questions', 5))

        test = ObjectiveTest(paragraph, num_questions)
        questions = test.generate_test()

        session['para_questions'] = questions
        session['para_paragraph'] = paragraph
        session['para_score'] = 0
        session['current_para_question'] = 0

        return redirect(url_for('show_para_question'))

    return render_template('paragraph_quiz_setup.html')


@app.route('/para-question')
def show_para_question():
    if 'current_para_question' not in session:
        return redirect(url_for('paragraph_quiz'))

    question = session['para_questions'][session['current_para_question']]
    return render_template(
        'para_question.html',
        paragraph=session['para_paragraph'],
        question=question['Question'],
        options=question['Options'],
        question_num=session['current_para_question'] + 1,
        total_questions=len(session['para_questions'])
    )


@app.route('/submit-para-answer', methods=['POST'])
def submit_para_answer():
    selected_answer = request.form.get('answer')
    correct_answer = session['para_questions'][session['current_para_question']]['Answer']

    if selected_answer == correct_answer:
        session['para_score'] += 1

    if session['current_para_question'] < len(session['para_questions']) - 1:
        session['current_para_question'] += 1
        return redirect(url_for('show_para_question'))
    else:
        return redirect(url_for('show_para_results'))


@app.route('/para-results')
def show_para_results():
    db = Database()
    try:
        db.execute_query(
            """INSERT INTO paragraph_quiz_results 
               (user_id, paragraph_text, total_questions, right_answers, wrong_answers)
               VALUES ((SELECT id FROM users WHERE username = %s), %s, %s, %s, %s)""",
            (session['username'], session['para_paragraph'],
             len(session['para_questions']), session['para_score'],
             len(session['para_questions']) - session['para_score'])
        )
    except Error as e:
        flash(f"Failed to save results: {str(e)}", "danger")

    return render_template(
        'para_results.html',
        score=session['para_score'],
        total=len(session['para_questions']),
        questions=session['para_questions'],
        paragraph=session['para_paragraph']
    )


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
