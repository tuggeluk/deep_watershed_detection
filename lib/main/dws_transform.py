from PIL import Image, ImageDraw

import sys
import math, random
from itertools import product
from utils.ufarray import *
import numpy as np
import cv2

def perform_dws(predict_dict,cutoff=0,min_ccoponent_size=0, config=None,  fatten_cutoff= 1):
    bbox_list = []

    dws_energy = np.squeeze(predict_dict["stamp_energy"])

    # Treshhold and binarize dws energy
    binar_energy = (dws_energy > cutoff) * 255

    # get connected components
    #labels, out_img = find_connected_comp(np.transpose(binar_energy)) # works with inverted indices
    # invert labels dict
    # labels_inv = {}
    # for k, v in labels.items():
    #     labels_inv[v] = labels_inv.get(v, [])
    #     labels_inv[v].append(k)
    #
    #
    # # filter components that are too small
    # for key in list(labels_inv):
    #     # print(key)
    #     # print(len(labels_inv[key]))
    #     if len(labels_inv[key]) < min_ccoponent_size:
    #         del labels_inv[key]

    retval, labels = cv2.connectedComponents(binar_energy.astype(np.uint8))

    for comp in range(1,retval):
        if np.sum(labels == comp) <  min_ccoponent_size:
            labels[labels == comp] = 0



    if "stamp_class" in predict_dict.keys():
        print("get classes")

    else:
        classes = np.ones(retval-1)

    if "stamp_bbox" in predict_dict.keys():
        print("boxes")
    else:
        print("boxes")
        # "fatten" the detected components using a cc analysis at cutoff 0
        binar_energy_0 = (dws_energy > fatten_cutoff) * 255
        retval_0, labels_0 = cv2.connectedComponents(binar_energy_0.astype(np.uint8))
        # iterate over cc_0 components
        for i in range(1, retval_0):
            support = np.unique(labels[labels_0 == i])
            # remove bg
            support = support[support != 0]
            # remove unusported components
            if len(support) > 0:
                # do nothing for support 0
                # replace pure components
                if len(support) == 1:
                    labels[labels_0 == i] = support[0]
                # deal with fused components
                else:
                    print(support)

                    coords_min = np.min(np.where(labels_0 == i), -1)
                    coords_max = np.max(np.where(labels_0 == i), -1)

                    patch = labels[coords_min[0]:coords_max[0], coords_min[1]:coords_max[1]]
                    dist_list = list()
                    for sup_ele in support:
                        dist_map = ((patch == sup_ele)-1)*-1E6
                        for direct in [1, -1, 2, -2]:
                            shape = dist_map.shape[np.abs(direct)-1]
                            if np.sign(direct) == 1:
                                rng = range(1, shape)
                            else:
                                rng = range(shape-2, -1, -1)

                            for ind in rng:
                                if np.abs(direct) == 1:
                                    dist_map[ind,:] = np.min(np.stack((dist_map[ind,:], dist_map[ind-np.sign(direct),:]+1),-1),-1)
                                else:
                                    dist_map[:,ind] = np.min(np.stack((dist_map[:,ind], dist_map[:,ind-np.sign(direct)]+1),-1),-1)
                        dist_list.append(dist_map)
                    dist_map = np.stack(dist_list, -1)
                    min_dist = np.argmin(dist_map, -1)
                    new_blobs = support[min_dist]
                    update_pix = labels_0[coords_min[0]:coords_max[0], coords_min[1]:coords_max[1]] != 0

                    # goal pane
                    labels[coords_min[0]:coords_max[0], coords_min[1]:coords_max[1]][update_pix] = new_blobs[update_pix]


        print("axis estimation")
        # from PIL import Image
        # Image.fromarray(labels.astype(np.uint8)*3).save("cc_fat.jpg")
        if config.bbox_angle == "estimated":
            print("estimate angle")
        else:
            est_angle = 0

        for i in np.unique(labels)[np.unique(labels)!=0]:
            coords_min = np.min(np.where(labels == i), -1)
            coords_max = np.max(np.where(labels == i), -1)
                            # xmin, ymin, xmax, ymax, class
            bbox_list.append([coords_min[1], coords_min[0], coords_max[1], coords_max[0], classes[i-1]])




    # class_map = np.squeeze(class_map)
    # bbox_map = np.squeeze(bbox_map)

    # for key in labels_inv.keys():
    #     # add additional dict structure to each component and convert to numpy array
    #     labels_inv[key] = dict(pixel_coords=np.asanyarray(labels_inv[key]))
    #     # use average over all pixel coordinates
    #     labels_inv[key]["center"] = np.average(labels_inv[key]["pixel_coords"],0).astype(int)
    #     # mayority vote for class --> transposed
    #     labels_inv[key]["class"] = np.bincount(class_map[labels_inv[key]["pixel_coords"][:, 1], labels_inv[key]["pixel_coords"][:, 0]]).argmax()
    #     # average for box size --> transposed
    #     #labels_inv[key]["bbox_size"] = np.average(bbox_map[labels_inv[key]["pixel_coords"][:, 1], labels_inv[key]["pixel_coords"][:, 0]],0).astype(int)
    #     labels_inv[key]["bbox_size"] = np.amax(
    #         bbox_map[labels_inv[key]["pixel_coords"][:, 1], labels_inv[key]["pixel_coords"][:, 0]], 0).astype(int)
    #
    #     # produce bbox element, append to list
    #     bbox = []
    #     bbox.append(int(np.round(labels_inv[key]["center"][0] - (labels_inv[key]["bbox_size"][1]/2.0), 0))) # xmin
    #     bbox.append(int(np.round(labels_inv[key]["center"][1] - (labels_inv[key]["bbox_size"][0]/2.0), 0))) # ymin
    #     bbox.append(int(np.round(labels_inv[key]["center"][0] + (labels_inv[key]["bbox_size"][1]/2.0), 0))) # xmax
    #     bbox.append(int(np.round(labels_inv[key]["center"][1] + (labels_inv[key]["bbox_size"][0]/2.0), 0))) # ymax
    #     bbox.append(int(labels_inv[key]["class"]))
    #     bbox_list.append(bbox)


    return bbox_list



def get_class(component,class_map):
    return None

def get_bbox(component,):
    return None

#
# Implements 8-connectivity connected component labeling
#
# Algorithm obtained from "Optimizing Two-Pass Connected-Component Labeling
# by Kesheng Wu, Ekow Otoo, and Kenji Suzuki
#
def find_connected_comp(input):
    data = input
    width, height = input.shape

    # Union find data structure
    uf = UFarray()

    #
    # First pass
    #

    # Dictionary of point:label pairs
    labels = {}

    for y, x in product(range(height), range(width)):

        #
        # Pixel names were chosen as shown:
        #
        #   -------------
        #   | a | b | c |
        #   -------------
        #   | d | e |   |
        #   -------------
        #   |   |   |   |
        #   -------------
        #
        # The current pixel is e
        # a, b, c, and d are its neighbors of interest
        #
        # 255 is white, 0 is black
        # White pixels part of the background, so they are ignored
        # If a pixel lies outside the bounds of the image, it default to white
        #

        # If the current pixel is white, it's obviously not a component...
        if data[x, y] == 255:
            pass

        # If pixel b is in the image and black:
        #    a, d, and c are its neighbors, so they are all part of the same component
        #    Therefore, there is no reason to check their labels
        #    so simply assign b's label to e
        elif y > 0 and data[x, y - 1] == 0:
            labels[x, y] = labels[(x, y - 1)]

        # If pixel c is in the image and black:
        #    b is its neighbor, but a and d are not
        #    Therefore, we must check a and d's labels
        elif x + 1 < width and y > 0 and data[x + 1, y - 1] == 0:

            c = labels[(x + 1, y - 1)]
            labels[x, y] = c

            # If pixel a is in the image and black:
            #    Then a and c are connected through e
            #    Therefore, we must union their sets
            if x > 0 and data[x - 1, y - 1] == 0:
                a = labels[(x - 1, y - 1)]
                uf.union(c, a)

            # If pixel d is in the image and black:
            #    Then d and c are connected through e
            #    Therefore we must union their sets
            elif x > 0 and data[x - 1, y] == 0:
                d = labels[(x - 1, y)]
                uf.union(c, d)

        # If pixel a is in the image and black:
        #    We already know b and c are white
        #    d is a's neighbor, so they already have the same label
        #    So simply assign a's label to e
        elif x > 0 and y > 0 and data[x - 1, y - 1] == 0:
            labels[x, y] = labels[(x - 1, y - 1)]

        # If pixel d is in the image and black
        #    We already know a, b, and c are white
        #    so simpy assign d's label to e
        elif x > 0 and data[x - 1, y] == 0:
            labels[x, y] = labels[(x - 1, y)]

        # All the neighboring pixels are white,
        # Therefore the current pixel is a new component
        else:
            labels[x, y] = uf.makeLabel()

    #
    # Second pass
    #

    uf.flatten()

    colors = {}

    # Image to display the components in a nice, colorful way
    output_img = Image.new("RGB", (width, height))
    outdata = output_img.load()

    for (x, y) in labels:

        # Name of the component the current point belongs to
        component = uf.find(labels[(x, y)])

        # Update the labels with correct information
        labels[(x, y)] = component

        # Associate a random color with this component
        if component not in colors:
            colors[component] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        # Colorize the image
        outdata[x, y] = colors[component]

    return (labels, output_img)