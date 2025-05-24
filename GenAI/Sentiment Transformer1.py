classifier = pipeline("text-classification", model = "tabularisai/multilingual-sentiment-analysis")

from transformers import pipeline
classifier = pipeline("text-classification", model = "tabularisai/multilingual-sentiment-analysis")

import pandas as pd

# Analyze for text1
outputs1 = classifier(text1)
pd.DataFrame(outputs1)