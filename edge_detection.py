import numpy as np

# this is not the real code, just a demo for the image pipeline
# this is a simplified canny edge detection code. it detects edges in the image

# create a random image with a size of (240, 160, 3)
img = np.randint(0, 255, (240, 160, 3))

# this is 5x5 gaussian kernel
def gaussian_filter(img):
	gaussian_kernel = np.array([
		[1,  4,  7,  4,  1],
		[4, 16, 26, 16,  4],
		[7, 26, 41, 26,  7],
		[4, 16, 26, 16,  4],
		[1,  4,  7,  4,  1],
	], np.float32) / 273

	return img.convolve(gaussian_kernel)

# sobel fitler typically uses to detect edges
def sobel_filter(img):
	x_filter = np.array(
		[[-1, 0, 1],
		 [-2, 0, 2],
		 [-1, 0, 1],
		],
		np.float32
	)

	y_filter = np.array(
		[[ 1,  2,  1],
		 [ 0,  0,  0],
		 [-1, -2, -1],
		],
		np.float32
	)

	# compute the gradient of each pixel in x and y direction
	x_grad = img.convolve(x_filter)
	y_grad = img.convolve(y_filter)

	# compute the hypotenuse of each pixel sqrt(x^2+y^2)
	grad = np.sqrt(x_grad**2 + y_grad**2)

	# compute the gradient direction
	angle = np.arctan2(y_grad, x_grad)

	return grad, angle

def non_max_filter(grad_img, angle):

	edge_img = np.zeros(grad_img.shape, np.float32)

	for c in range(grad_img.shape[0]):
		for r in range(grad_img.shape[1]):
			ang = angle[c, r]

			head = 255
			tail = 255
			if ang < 22.5 or ang >= 157.5:
				head = grad_img[c, r+1]
				tail = grad_img[c, r-1]
			elif 22.5 <= ang < 67.5:
				head = grad_img[c+1, r-1]
				tail = grad_img[c-1, r+1]
			elif 67.5 <= ang < 112.5:
				head = grad_img[c+1, r]
				tail = grad_img[c-1, r]
			else:
				head = grad_img[c-1, r-1]
				tail = grad_img[c+1, r+1]

			if grad_img[c, r] >= head and grad_img[c, r] >= tail:
				ret_img[c, r] = 255
			else:
				ret_img[c, r] = 0

	return edge_img

smoothed_img = gaussian_filter(img)
grad_img, angle = sobel_filter(smoothed_img)
edge_img = non_max_filter(grad_img, angle)










