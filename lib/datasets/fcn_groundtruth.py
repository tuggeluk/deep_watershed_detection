# --------------------------------------------------------
# Licensed under The MIT License [see LICENSE for details]
# Written by Lukas Tuggener
# --------------------------------------------------------


from PIL import Image, ImageDraw
import numpy as np


def objectness_energy(data, gt_boxes):
    objectness = np.zeros(data[0].shape[0:2], dtype=np.int16)-10
    mark = objectness_marker(4, 4, func_nothing)

    for row in gt_boxes:
        center_1 = np.round((row[2]-row[0])/2 + row[0])
        center_0 = np.round((row[3] - row[1]) / 2 + row[1])

        objectness[int(center_0-mark.shape[0]/2):int(center_0+mark.shape[0]/2+1),
        int(center_1 - mark.shape[1] / 2):int(center_1 + mark.shape[1] / 2)+1] = mark

    return objectness

def objectness_energy_high_dym(data, gt_boxes, num_classes):
    objectness = np.zeros([data[0].shape[0],data[0].shape[1],num_classes], dtype=np.int16) - 10
    mark = objectness_marker(4, 4, func_nothing)

    for row in gt_boxes:
        center_1 = np.round((row[2]-row[0])/2 + row[0])
        center_0 = np.round((row[3] - row[1]) / 2 + row[1])

        objectness[int(center_0-mark.shape[0]/2):int(center_0+mark.shape[0]/2+1),
        int(center_1 - mark.shape[1] / 2):int(center_1 + mark.shape[1] / 2)+1, int(row[4])] = mark

    return objectness


def func_nothing(grid):
    return grid


def func_square(grid):
    return np.square(grid)


def objectness_marker(sx=3,sy=3,fnc=func_nothing):
    grid_x = np.concatenate((range(sx),range(sx,-1,-1)))
    grid_y = np.concatenate((range(sy),range(sy,-1,-1)))
    exec_grid = np.min(np.stack(np.meshgrid(grid_x, grid_y)),0)
    return fnc(exec_grid)

# pil_im = Image.fromarray(im)
def show_image(data, gt_boxes=None, gt=False):
    im = Image.fromarray(data[0].astype("uint8"))
    im.show()

    if gt:
        draw = ImageDraw.Draw(im)
        # overlay GT boxes
        for row in gt_boxes:
            draw.rectangle(((row[0],row[1]),(row[2],row[3])), fill="red")
        im.show()
    return