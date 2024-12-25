# prompt: In the above animation, the rectangle sound only appears up to the respective degree. It should not overlap with the previous rectangle. and limitation on underfitting is 0 to 2.5 in width, good model is 2.5 to 5.5 in width, and for overfitting is 5.5 to 15. Give me the entire code once again.

import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import mean_squared_error
import matplotlib.animation as animation
from sklearn.metrics import r2_score
from matplotlib.patches import Rectangle
import matplotlib.style as style

style.use('dark_background')

# Generate synthetic data
np.random.seed(42)
x_train = np.random.uniform(0, 10, 20)
y_train = 2 + 0.5 * x_train**2 - 0.3 * x_train + np.random.normal(0, 4, len(x_train))

x_test = np.random.uniform(0, 10, 20)
y_test = 2 + 0.5 * x_test**2 - 0.3 * x_test + np.random.normal(0, 4, len(x_test))

x_train = x_train[:, np.newaxis]
x_test = x_test[:, np.newaxis]

# Initialize figures and axes
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 15))
x_range = np.linspace(0, 10, 200).reshape(-1, 1)

# Plot for Polynomial Degree
train_scatter1 = ax1.scatter(x_train, y_train, color="cyan", label="Training Data")
test_scatter1 = ax1.scatter(x_test, y_test, color="lime", label="Testing Data")
curve1, = ax1.plot([], [], color="red", label="Model Curve")
ax1.legend()
ax1.set_xlim(0, 10)
ax1.set_ylim(0, 60)
ax1.set_xlabel("Weight")
ax1.set_ylabel("Height")

# Plot for MSE
train_errors = []
test_errors = []
line_train, = ax2.plot([], [], label="Training Error", marker="o", color="orange")
line_test, = ax2.plot([], [], label="Testing Error", marker="o", color="magenta")
ax2.set_xlabel("Polynomial Degree")
ax2.set_ylabel("Mean Squared Error")
ax2.set_title("Bias-Variance Tradeoff")
ax2.legend()
ax2.set_xlim(0, 15)
ax2.set_ylim(0, 50)

# Plot for Adjusted R-squared
adjusted_r2_values_train = []
adjusted_r2_values_test = []
line_adjusted_r2_train, = ax3.plot([], [], label="Training Adjusted R-squared", marker="o", color="purple")
line_adjusted_r2_test, = ax3.plot([], [], label="Testing Adjusted R-squared", marker="o", color="yellow")
ax3.set_xlabel("Polynomial Degree")
ax3.set_ylabel("Adjusted R-squared")
ax3.set_title("Model Performance")
ax3.legend()
ax3.set_xlim(0, 15)
ax3.set_ylim(0.6, 1)

# Initialize rectangles
rect1 = Rectangle((0, 0), 2.5, 1, alpha=0.3, color='red', label='Underfitting')
rect2 = Rectangle((2.5, 0), 3, 1, alpha=0.3, color='green', label='Good Model')
rect3 = Rectangle((5.5, 0), 9.5, 1, alpha=0.3, color='orange', label='Overfitting')
ax3.add_patch(rect1)
ax3.add_patch(rect2)
ax3.add_patch(rect3)

def update(degree):
    global train_errors, test_errors, adjusted_r2_values_train, adjusted_r2_values_test, rect1, rect2, rect3
    ax1.set_title(f"Polynomial Degree: {degree}")

    poly = PolynomialFeatures(degree=degree)
    x_poly_train = poly.fit_transform(x_train)
    x_poly_test = poly.transform(x_test)
    x_poly_range = poly.transform(x_range)

    model = LinearRegression()
    model.fit(x_poly_train, y_train)

    y_pred_train = model.predict(x_poly_train)
    y_pred_test = model.predict(x_poly_test)
    y_pred_range = model.predict(x_poly_range)

    train_error = mean_squared_error(y_train, y_pred_train)
    test_error = mean_squared_error(y_test, y_pred_test)

    train_errors.append(train_error)
    test_errors.append(test_error)

    curve1.set_data(x_range, y_pred_range)
    line_train.set_data(range(1, len(train_errors) + 1), train_errors)
    line_test.set_data(range(1, len(test_errors) + 1), test_errors)
    ax2.relim()
    ax2.autoscale_view()

    n_train = len(y_train)
    n_test = len(y_test)
    p = degree
    r2_train = r2_score(y_train, y_pred_train)
    r2_test = r2_score(y_test, y_pred_test)
    adjusted_r2_train = 1 - (1 - r2_train) * (n_train - 1) / (n_train - p - 1) if (n_train - p - 1) > 0 else np.nan
    adjusted_r2_test = 1 - (1 - r2_test) * (n_test - 1) / (n_test - p - 1) if (n_test - p - 1) > 0 else np.nan

    adjusted_r2_values_train.append(adjusted_r2_train)
    adjusted_r2_values_test.append(adjusted_r2_test)

    line_adjusted_r2_train.set_data(range(1, len(adjusted_r2_values_train) + 1), adjusted_r2_values_train)
    line_adjusted_r2_test.set_data(range(1, len(adjusted_r2_values_test) + 1), adjusted_r2_values_test)
    ax3.relim()
    ax3.autoscale_view()

    rect1.set_width(min(degree, 2.5))
    rect2.set_width(min(max(0, degree - 2.5), 3))
    rect3.set_width(min(max(0, degree-5.5), 9.5))

    if degree == 1:
        handles, labels = ax1.get_legend_handles_labels()
        ax3.legend(handles + [rect1, rect2, rect3], labels + ['Underfitting', 'Good Model', 'Overfitting'])

    return curve1, line_train, line_test, line_adjusted_r2_train, line_adjusted_r2_test, rect1, rect2, rect3

ani = animation.FuncAnimation(fig, update, frames=range(1, 16), interval=1000, blit=False)
ani.save("bias_variance_animation_dark.gif", writer="pillow")
plt.tight_layout()
plt.show()