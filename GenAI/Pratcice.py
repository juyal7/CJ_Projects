# Import necessary libraries
import string
import random
import nltk
from nltk import FreqDist
from nltk.corpus import brown
from collections import defaultdict, Counter
from nltk.util import ngrams

# Download necessary NLTK packages and corpus
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('brown')# Define stopwords and punctuation
stop_words = set(nltk.corpus.stopwords.words('english'))
string.punctuation += '"\'-—'
removal_list = list(stop_words) + list(string.punctuation) + ['lt', 'rt']# Load sentences from the Brown corpus
sents = brown.sents()

# Initialize lists for storing n-grams
unigram = []
bigram = []
trigram = []

# Generate n-grams
for sentence in sents:
    sentence = [word.lower() for word in sentence if word not in string.punctuation]
    unigram.extend(sentence)
    bigram.extend(list(ngrams(sentence, 2, pad_left=False, pad_right=False)))
    trigram.extend(list(ngrams(sentence, 3, pad_left=False, pad_right=False)))
    
# Function to remove stopwords from n-grams
def remove_stopwords(ngrams, n):
    if n == 2:
        return [(a, b) for (a, b) in ngrams if a not in removal_list and b not in removal_list]
    elif n == 3:
        return [(a, b, c) for (a, b, c) in ngrams if a not in removal_list and b not in removal_list and c not in removal_list]

# Remove stopwords from n-grams
bigram = remove_stopwords(bigram, 2)
trigram = remove_stopwords(trigram, 3)

# Calculate frequency distributions
freq_bi = FreqDist(bigram)
freq_tri = FreqDist(trigram)

# Create a dictionary of trigram frequencies with a threshold for filtering
threshold = 2  # Minimum frequency for trigrams to be included
d = defaultdict(Counter)
for ngram, freq in freq_tri.items():
    if freq >= threshold:
        d[ngram[:-1]][ngram[-1]] += freq
# Function to generate text with enhanced logic
def generate_text(prefix, n=20):
    text = list(prefix)
    for _ in range(n):
        suffix_candidates = list(d.get(prefix, Counter()).elements())
        if not suffix_candidates:
            # Choose a new prefix from the dictionary keys if no candidates
            prefix = random.choice(list(d.keys()))
        else:
            # Choose a suffix and update the prefix
            suffix = random.choice(suffix_candidates)
            text.append(suffix)
            prefix = (*prefix[1:], suffix)
    return " ".join(text)
# Generate text with a random valid prefix
prefix = random.choice(list(d.keys()))  # Randomly select a valid prefix
generated_text = generate_text(prefix, n=50)  # Generate text of 50 words
print("Generated Text:", generated_text)