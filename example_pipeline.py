import numpy as np
import tensorflow as tf

# create a random image with a size of (240, 160, 3)
img = np.randint(0, 255, (240, 160, 3))

denoised_img = np.zeros(img.shape)
# perform a mean filter to denoise
for c in range(image.shape[0]):
    for r in range(image.shape[1]):
        for i in range(image.shape[2]):
            denoised_img[c, r, i] = (
                                            img[c - 1, r - 1, i] + img[c - 1, r, i] + img[c - 1, r + 1, i]
                                            + img[c, r - 1, i] + img[c, r, i] + img[c, r + 1, i]
                                            + img[c + 1, r - 1, i] + img[c + 1, r, i] + img[c + 1, r + 1, i]
                                    ) / 9

white_balanced_img = np.zeros(img.shape)
# perform white-patch algorithm in white balance stage
for i in range(denoised_img.shape[2]):
    max_val = np.max(denoised_img[:, :, i])
    white_balanced_img[:, :, i] = denoised_img[:, :, i] / max_val * 255

# perform conv with a (3x3x32) kernel with a strike of 2
weight1 = tf.tensor((3, 3, 32))
feature1 = tf.conv2D(white_balanced_img, kernel=weight1, strike=2)  # output (120, 80, 32)

# perform conv with a (3x3x32) kernel with a strike of 2
weight2 = tf.tensor((3, 3, 32))
feature2 = tf.conv2D(feature1, kernel=weight2, strike=2)  # output (60, 40, 32)

# perform conv with a (3x3x1) kernel with a strike of 2
weight3 = tf.tensor((3, 3, 1))
feature3 = tf.conv2D(feature2, kernel=weight3, strike=2)  # output (30, 20, 1)

feature3 = tf.flatten((600, 1))  # flatten the feature to (600, 1)

# perform Matrix-matrix multipication
weight4 = tf.tensor((600, 10))
output = tf.fc(feature3, kernel=weight4)
