import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from sklearn.datasets import make_moons
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from tensorflow.keras import Input, Model
from tensorflow.keras.layers import Dense

# Generate non-linear dataset
X, y = make_moons(n_samples=1000, noise=0.2, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Normalize features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ReLU Model
model_relu = tf.keras.Sequential([
    tf.keras.layers.Dense(16, activation='relu', input_shape=(2,)),
    tf.keras.layers.Dense(16, activation='relu'),
    tf.keras.layers.Dense(1, activation='sigmoid')
])

inputs = Input(shape=(2,))

x = Dense(16, activation='relu')(inputs)
x = Dense(16, activation='relu')(x)
outputs = Dense(1, activation='sigmoid')(x)

model_relu = Model(inputs=inputs, outputs=outputs)

model_relu.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

history_relu = model_relu.fit(X_train_scaled, y_train, epochs=30, batch_size=32, validation_data=(X_test_scaled, y_test), verbose=0)

acc_relu = model_relu.evaluate(X_test_scaled, y_test)[1]
print(f"Validation Accuracy with ReLU: {acc_relu:.2f}")

# Plot comparison
plt.plot(history_relu.history['val_accuracy'], label='ReLU')
plt.title("Validation Accuracy over Epochs")
plt.xlabel("Epochs")
plt.ylabel("Accuracy")
plt.legend()
plt.grid(True)
plt.show()
