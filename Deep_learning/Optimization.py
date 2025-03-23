import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import tensorflow as tf
from tensorflow.keras.optimizers import SGD, Adam, RMSprop, Adagrad, Adadelta, Adamax, Nadam
from tensorflow.keras.layers import Dense, Input
from tensorflow.keras.models import Sequential
from livelossplot import PlotLossesKerasTF
from tensorflow.keras.metrics import Precision, Recall
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Load data
df = pd.read_csv("C:/Users/Chanchal Juyal/Desktop/My Work/Learning Docs/AIML/Classes/Deep_Learning/Day5/gold_fund.csv")
print(df.head())

x = df.drop(columns=['ID', 'Gold_Fund'])
y = df.Gold_Fund

# Split and standardize the data
x_train, x_test, y_train, y_test = train_test_split(x, y, random_state=0)

st = StandardScaler()
x_train_std = st.fit_transform(x_train)
x_test_std = st.fit_transform(x_test)

# Define optimizers to compare
optimizers = {
    'SGD': SGD(learning_rate=0.01, momentum=0.9),
    'Adam': Adam(learning_rate=0.001),
    'RMSprop': RMSprop(learning_rate=0.001),
    'Adagrad': Adagrad(learning_rate=0.01),
    'Adadelta': Adadelta(learning_rate=1.0),
    'Adamax': Adamax(learning_rate=0.002),
    'Nadam': Nadam(learning_rate=0.002)
}

# Function to create the model with the same architecture
def create_model():
    model = Sequential()
    model.add(Input(shape=(15,)))
    model.add(Dense(20, activation='relu'))
    model.add(Dense(20, activation='relu'))
    model.add(Dense(1, activation='sigmoid'))
    return model

# Train with each optimizer and store results
results = {}
histories = {}

for name, optimizer in optimizers.items():
    print(f"\n\n{'='*50}")
    print(f"Training with {name} optimizer")
    print(f"{'='*50}\n")
    
    # Create a new model for each optimizer
    model = create_model()
    
    # Compile the model
    model.compile(
        loss='binary_crossentropy',
        optimizer=optimizer,
        metrics=['accuracy', Precision(), Recall()]
    )
    
    # Create a custom callback to save history
    history = model.fit(
        x_train_std, y_train,
        epochs=100,
        batch_size=64,
        callbacks=[PlotLossesKerasTF()],
        validation_data=(x_test_std, y_test),
        verbose=1
    )
    
    # Store the training history
    histories[name] = history.history
    
    # Evaluate on test set
    test_results = model.evaluate(x_test_std, y_test, verbose=0)
    results[name] = {
        'test_loss': test_results[0],
        'test_accuracy': test_results[1],
        'test_precision': test_results[2],
        'test_recall': test_results[3]
    }

# Convert results to a DataFrame for easier comparison
results_df = pd.DataFrame(results).T
print("\nFinal Results:")
print(results_df)

# Plot comparison of training histories
# plt.figure(figsize=(20, 15))

# # Plot training & validation accuracy
# plt.subplot(2, 2, 1)
# for name, history in histories.items():
#     plt.plot(history['accuracy'], linestyle='-', label=f'{name} Train')
# plt.title('Training Accuracy')
# plt.xlabel('Epoch')
# plt.ylabel('Accuracy')
# plt.legend()

# plt.subplot(2, 2, 2)
# for name, history in histories.items():
#     plt.plot(history['val_accuracy'], linestyle='--', label=f'{name} Val')
# plt.title('Validation Accuracy')
# plt.xlabel('Epoch')
# plt.ylabel('Accuracy')
# plt.legend()

# # Plot training & validation loss
# plt.subplot(2, 2, 3)
# for name, history in histories.items():
#     plt.plot(history['loss'], linestyle='-', label=f'{name} Train')
# plt.title('Training Loss')
# plt.xlabel('Epoch')
# plt.ylabel('Loss')
# plt.legend()

# plt.subplot(2, 2, 4)
# for name, history in histories.items():
#     plt.plot(history['val_loss'], linestyle='--', label=f'{name} Val')
# plt.title('Validation Loss')
# plt.xlabel('Epoch')
# plt.ylabel('Loss')
# plt.legend()

# plt.tight_layout()
# plt.savefig('optimizer_comparison.png')
# plt.show()

# Create a bar chart to compare final metrics
metrics = ['test_accuracy', 'test_precision', 'test_recall']
plt.figure(figsize=(15, 10))

# for i, metric in enumerate(metrics):
#     plt.subplot(1, 3, i+1)
#     plt.bar(results_df.index, results_df[metric])
#     plt.title(f'Test {metric.split("_")[1].capitalize()}')
#     plt.xticks(rotation=45)
#     plt.ylim(0, 1)

# plt.tight_layout()
# plt.savefig('optimizer_metrics_comparison.png')
# plt.show()

# Print summary of the best optimizer for each metric
print("\nBest optimizer for each metric:")
for metric in metrics:
    best = results_df[metric].idxmax()
    print(f"{metric.split('_')[1].capitalize()}: {best} ({results_df.loc[best, metric]:.4f})")