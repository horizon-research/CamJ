from reverse_process import unprocess
from forward_process import process, process_only_gain, process_no_demosaic
import cv2
import os
import random
import numpy as np
import tensorflow as tf

def get_luminance(raw_img):
	gaussian_filter = [
		[-2,  3, -6,  3, -2],
		[ 3,  4,  2,  4,  3],
		[-6,  2, 48,  2,  6],
		[ 3,  4,  2,  4,  3],
		[-2,  3, -6,  3, -2]
	]

	luminance = np.zeros(raw_img.shape)
	H, W = raw_img.shape

	for r in range(5):
		for c in range(5):
			r_offset = 2 - r
			c_offset = 2 - c
			luminance[int(max(r_offset, 0)):int(min(r_offset+H, H)), int(max(c_offset, 0)):int(min(c_offset+W, W))]= \
				raw_img[int(max(-r_offset, 0)):int(min(-r_offset+H, H)), int(max(-c_offset, 0)):int(min(-c_offset+W, W))]*gaussian_filter[r][c]

	return luminance / 64.


def perform_chorma_bilinear(luminance, red, green, blue):
	H, W = luminance.shape
	lumin_red = red
	lumin_red = cv2.resize(luminance[0::2, 0::2] - red[0::2, 0::2], (W, H))
	
	lumin_green = green
	lumin_green = (
		cv2.resize(
			luminance[1::2, 0::2] - green[1::2, 0::2],
			(W, H)
		) + cv2.resize(
			luminance[0::2, 1::2] - green[0::2, 1::2],
			(W, H)
		)
	) / 2.

	lumin_blue = blue
	lumin_blue = cv2.rotate(
		cv2.resize(
			cv2.rotate(
				luminance[1::2, 1::2] - blue[1::2, 1::2],
				cv2.ROTATE_180
			), 
			(W, H)
		),
		cv2.ROTATE_180
	)

	red = luminance - lumin_red
	green = luminance - lumin_green
	blue = luminance - lumin_blue

	rgb_img = np.zeros((H, W, 3))
	rgb_img[:, :, 0] = red
	rgb_img[:, :, 1] = green
	rgb_img[:, :, 2] = blue

	return rgb_img

def lumin_based_interpolation(raw_rggb):
	H, W, _ = raw_rggb.shape

	raw_img = np.zeros((H*2, W*2))
	rgb_img = np.zeros((H*2, W*2, 3))

	raw_img[0::2, 0::2] = raw_rggb[:, :, 0]
	raw_img[1::2, 0::2] = raw_rggb[:, :, 1]
	raw_img[0::2, 1::2] = raw_rggb[:, :, 2]
	raw_img[1::2, 1::2] = raw_rggb[:, :, 3]

	rgb_img[0::2, 0::2, 0] = raw_rggb[:, :, 0]
	rgb_img[1::2, 0::2, 1] = raw_rggb[:, :, 1]
	rgb_img[0::2, 1::2, 1] = raw_rggb[:, :, 2]
	rgb_img[1::2, 1::2, 2] = raw_rggb[:, :, 3]

	luminance = get_luminance(raw_img)

	rgb_img = perform_chorma_bilinear(luminance, rgb_img[:, :, 0], rgb_img[:, :, 1], rgb_img[:, :, 2])

	return rgb_img

def edge_aware_interpolation_green_channel(green_channel):
	(H, W) = green_channel.shape
	# auto fill first and last row
	for i in range(W):
		if [0, i] == 0:
			green_channel[0, i] = green_channel[1, i]
		if green_channel[-1, i] == 0:
			green_channel[-1, i] = green_channel[-2, i]

	# auto fill first and last column
	for i in range(H):
		if green_channel[i, 0] == 0:
			green_channel[i, 0] = green_channel[i, 1]
		if green_channel[i, -1] == 0:
			green_channel[i, -1] = green_channel[i, -2]

	# edge aware interpolation first green
	for i in range(H//2):
		for j in range(W//2):
			r = i*2
			c = j*2
			# skip those rows and cols
			if r == 0 or c == 0 or r >= H-1 or c >= W-1:
				continue
			
			delta_h = np.abs(green_channel[r, c-1] - green_channel[r, c+1])
			delta_v = np.abs(green_channel[r-1, c] - green_channel[r+1, c])

			if delta_h > delta_v:
				green_channel[r, c] = 1/2*(green_channel[r-1, c]+green_channel[r+1, c])
			else:
				green_channel[r, c] = 1/2*(green_channel[r, c-1]+green_channel[r, c+1])

	# edge aware interpolation second green
	for i in range(H//2):
		for j in range(W//2):
			r = i*2+1
			c = j*2+1
			# skip those rows and cols
			if r >= H-1 or c >= W-1:
				continue
			
			delta_h = np.abs(green_channel[r, c-1] - green_channel[r, c+1])
			delta_v = np.abs(green_channel[r-1, c] - green_channel[r+1, c])

			if delta_h > delta_v:
				green_channel[r, c] = 1/2*(green_channel[r-1, c]+green_channel[r+1, c])
			else:
				green_channel[r, c] = 1/2*(green_channel[r, c-1]+green_channel[r, c+1])


	# cv2.imshow("green_channel", green_channel/np.max(green_channel))
	# cv2.waitKey(0)
	# cv2.destroyAllWindows()

	return green_channel


def edge_aware_interpolation_red_channel(red_channel):
	(H, W) = red_channel.shape
	# print(red_channel)
	red_channel[1::2, -1] = red_channel[0::2, -2]
	red_channel[-1:, 1::2] = red_channel[-2, 0::2]

	# R22 interpolation
	for i in range(H//2):
		for j in range(W//2):
			r = i*2+1
			c = j*2+1
			# skip those rows and cols
			if r >= H-1 or c >= W-1:
				continue
			red_channel[r, c] = 1/4*(
				red_channel[r-1, c-1]+red_channel[r-1, c+1]+
				red_channel[r+1, c-1]+red_channel[r+1, c+1])

	# print(red_channel)

	# auto fill first and last row
	for i in range(W):
		if [0, i] == 0:
			red_channel[0, i] = red_channel[1, i]
		if red_channel[-1, i] == 0:
			red_channel[-1, i] = red_channel[-2, i]

	# auto fill first and last column
	for i in range(H):
		if red_channel[i, 0] == 0:
			red_channel[i, 0] = red_channel[i, 1]
		if red_channel[i, -1] == 0:
			red_channel[i, -1] = red_channel[i, -2]

	# edge aware interpolation first red
	for i in range(H//2):
		for j in range(W//2):
			r = i*2+1
			c = j*2
			# skip those rows and cols
			if r == 0 or c == 0 or r >= H-1 or c >= W-1:
				continue
			
			delta_h = np.abs(red_channel[r, c-1] - red_channel[r, c+1])
			delta_v = np.abs(red_channel[r-1, c] - red_channel[r+1, c])

			if delta_h > delta_v:
				red_channel[r, c] = 1/2*(red_channel[r-1, c]+red_channel[r+1, c])
			else:
				red_channel[r, c] = 1/2*(red_channel[r, c-1]+red_channel[r, c+1])

	# edge aware interpolation second green
	for i in range(H//2):
		for j in range(W//2):
			r = i*2
			c = j*2+1
			# skip those rows and cols
			if r >= H-1 or c >= W-1:
				continue
			
			delta_h = np.abs(red_channel[r, c-1] - red_channel[r, c+1])
			delta_v = np.abs(red_channel[r-1, c] - red_channel[r+1, c])

			if delta_h > delta_v:
				red_channel[r, c] = 1/2*(red_channel[r-1, c]+red_channel[r+1, c])
			else:
				red_channel[r, c] = 1/2*(red_channel[r, c-1]+red_channel[r, c+1])

	# cv2.imshow("red_channel", red_channel/np.max(red_channel))
	# cv2.waitKey(0)
	# cv2.destroyAllWindows()

	return red_channel


def edge_aware_interpolation_blue_channel(blue_channel):
	(H, W) = blue_channel.shape
	blue_channel[0::2, 0] = blue_channel[1::2, 1]
	blue_channel[0:, 0::2] = blue_channel[1, 1::2]

	# B11 interpolation
	for i in range(H//2):
		for j in range(W//2):
			r = i*2
			c = j*2
			# skip those rows and cols
			if c == 0 or r == 0 or r >= H-1 or c >= W-1:
				continue
			blue_channel[r, c] = 1/4*(
				blue_channel[r-1, c-1]+blue_channel[r-1, c+1]+
				blue_channel[r+1, c-1]+blue_channel[r+1, c+1]
			)

	# auto fill first and last row
	for i in range(W):
		if [0, i] == 0:
			blue_channel[0, i] = blue_channel[1, i]
		if blue_channel[-1, i] == 0:
			blue_channel[-1, i] = blue_channel[-2, i]

	# auto fill first and last column
	for i in range(H):
		if blue_channel[i, 0] == 0:
			blue_channel[i, 0] = blue_channel[i, 1]
		if blue_channel[i, -1] == 0:
			blue_channel[i, -1] = blue_channel[i, -2]

	# edge aware interpolation first blue
	for i in range(H//2):
		for j in range(W//2):
			r = i*2+1
			c = j*2
			# skip those rows and cols
			if r == 0 or c == 0 or r >= H-1 or c >= W-1:
				continue
			
			delta_h = np.abs(blue_channel[r, c-1] - blue_channel[r, c+1])
			delta_v = np.abs(blue_channel[r-1, c] - blue_channel[r+1, c])

			if delta_h > delta_v:
				blue_channel[r, c] = 1/2*(blue_channel[r-1, c]+blue_channel[r+1, c])
			else:
				blue_channel[r, c] = 1/2*(blue_channel[r, c-1]+blue_channel[r, c+1])

	# edge aware interpolation second green
	for i in range(H//2):
		for j in range(W//2):
			r = i*2
			c = j*2+1
			# skip those rows and cols
			if r >= H-1 or c >= W-1:
				continue
			
			delta_h = np.abs(blue_channel[r, c-1] - blue_channel[r, c+1])
			delta_v = np.abs(blue_channel[r-1, c] - blue_channel[r+1, c])

			if delta_h > delta_v:
				blue_channel[r, c] = 1/2*(blue_channel[r-1, c]+blue_channel[r+1, c])
			else:
				blue_channel[r, c] = 1/2*(blue_channel[r, c-1]+blue_channel[r, c+1])

	# cv2.imshow("blue_channel", blue_channel/np.max(blue_channel))
	# cv2.waitKey(0)
	# cv2.destroyAllWindows()

	return blue_channel

def edge_aware_interpolation(bayer_img):
	(H, W, _) = bayer_img.shape
	rgb_img = np.zeros((H*2, W*2, 3))

	rgb_img[0::2, 0::2, 0] = bayer_img[:, :, 0]
	rgb_img[1::2, 0::2, 1] = bayer_img[:, :, 1]
	rgb_img[0::2, 1::2, 1] = bayer_img[:, :, 2]
	rgb_img[1::2, 1::2, 2] = bayer_img[:, :, 3]

	# print(np.mean(bayer_img[:, :, 0]), np.mean(bayer_img[:, :, 1]), np.mean(bayer_img[:, :, 2]), np.mean(bayer_img[:, :, 3]))
	rgb_img[:, :, 1] = edge_aware_interpolation_green_channel(rgb_img[:, :, 1])
	rgb_img[:, :, 0] = edge_aware_interpolation_red_channel(rgb_img[:, :, 0])
	rgb_img[:, :, 2] = edge_aware_interpolation_blue_channel(rgb_img[:, :, 2])

	return rgb_img

def opencv_demosaic(bayer_img):
	(H, W, _) = bayer_img.shape
	raw_img = np.zeros((H*2, W*2))

	raw_img[0::2, 0::2] = bayer_img[:, :, 0]
	raw_img[0::2, 1::2] = bayer_img[:, :, 1]
	raw_img[1::2, 0::2] = bayer_img[:, :, 2]
	raw_img[1::2, 1::2] = bayer_img[:, :, 3]
	raw_img = (raw_img*256).astype(np.uint8)

	bgr_img = cv2.cvtColor(raw_img, cv2.COLOR_BayerBG2RGB)
	return bgr_img/np.max(bgr_img)

def low_pass_chroma(img):
	restored_img = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)

	restored_img[:, :, 1] = cv2.medianBlur(restored_img[:, :, 1], 5)
	restored_img[:, :, 2] = cv2.medianBlur(restored_img[:, :, 2], 5)
	
	restored_img = cv2.cvtColor(restored_img, cv2.COLOR_YUV2BGR)

	return restored_img

def edge_aware_demosaic(raw_img, metadata):

	raw_img = tf.expand_dims(raw_img, axis=0)
	bayer_img = process_only_gain(raw_img, metadata["red_gain"], metadata["blue_gain"])

	bayer_img = bayer_img.numpy()

	demosaic_img = edge_aware_interpolation(bayer_img[0])

	demosaic_img = tf.expand_dims(tf.convert_to_tensor(demosaic_img, dtype=tf.float32), axis=0)

	restored_img = process_no_demosaic(demosaic_img, metadata["cam2rgb"])

	restored_img = restored_img.numpy()[0]

	restored_img = low_pass_chroma(restored_img)

	return restored_img

def luminance_based_demosaic(raw_img, metadata):
	raw_img = tf.expand_dims(raw_img, axis=0)
	bayer_img = process_only_gain(raw_img, metadata["red_gain"], metadata["blue_gain"])

	bayer_img = bayer_img.numpy()[0]
	demosaic_img = lumin_based_interpolation(bayer_img)

	demosaic_img = tf.expand_dims(tf.convert_to_tensor(demosaic_img, dtype=tf.float32), axis=0)

	restored_img = process_no_demosaic(demosaic_img, metadata["cam2rgb"])

	restored_img = restored_img.numpy()[0]

	restored_img = low_pass_chroma(restored_img)
	return restored_img

def chroma_filter_demosaic(raw_img, metadata):
	raw_img = tf.expand_dims(raw_img, axis=0)
	restored_img = process(raw_img, metadata["red_gain"], metadata["blue_gain"], metadata["cam2rgb"])

	restored_img = restored_img.numpy()[0]

	restored_img = low_pass_chroma(restored_img)

	return restored_img

def convert_raw(bayer_img):

	(H, W, _) = bayer_img.shape
	raw_img = np.zeros((H*2, W*2))

	raw_img[0::2, 0::2] = bayer_img[:, :, 0]
	raw_img[1::2, 0::2] = bayer_img[:, :, 1]
	raw_img[0::2, 1::2] = bayer_img[:, :, 2]
	raw_img[1::2, 1::2] = bayer_img[:, :, 3]

	return raw_img

def convert_bayer(raw_img):

	(H, W) = raw_img.shape
	bayer_img = np.zeros((H//2, W//2, 4))

	bayer_img[:, :, 0] = raw_img[0::2, 0::2]
	bayer_img[:, :, 1] = raw_img[1::2, 0::2]
	bayer_img[:, :, 2] = raw_img[0::2, 1::2]
	bayer_img[:, :, 3] = raw_img[1::2, 1::2]

	return bayer_img