import numpy as np
import math
import os
import cv2
import time
import random
import tensorflow as tf

from reverse_process import unprocess
from forward_process import process, process_only_gain, process_no_demosaic
from isp_utils import convert_raw, convert_bayer, edge_aware_demosaic, \
                      luminance_based_demosaic, chroma_filter_demosaic
def main():
    # read the image file
    img_name = "example.jpg"
    print("processing %s" % (img_name))
    # load test image
    org_img = np.array(cv2.imread(img_name, cv2.IMREAD_COLOR), dtype=np.float32)/255.

    # trim the image to be multiple of 2
    (H, W, _) = org_img.shape
    org_img = org_img[:(H//2)*2, :(W//2)*2, :]

    # convert to tensor for tf reverse process
    org_img = tf.convert_to_tensor(org_img, dtype=tf.float32)

    # reverse process and generate raw bayer image (H//2, W//2, 4)
    # 4 is for RGGB
    bayer_raw, metadata = unprocess(org_img)
    # convert bayer image to raw image (H, W)
    raw_img = convert_raw(bayer_raw)

    # forward process, first convert to bayer image
    noise_bayer = convert_bayer(raw_img)
    noise_bayer = tf.convert_to_tensor(noise_bayer, dtype=tf.float32)

    # perform demosaicing, there are several different demosaicing methods as shown in `isp_utils`
    restored_img = chroma_filter_demosaic(noise_bayer, metadata)

    # clip the value into [0, 1), if store the image please convert to [0, 256)
    restored_img = np.clip(restored_img, 0, 1)
    cv2.imshow("restored_img", restored_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()


