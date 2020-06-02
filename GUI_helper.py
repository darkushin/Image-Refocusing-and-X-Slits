import cv2
import numpy as np
from tkinter import *
import tkinter as tk
from PIL import Image, ImageTk
import os
import matplotlib.pyplot as plt


def load_images(dir):
    """
    Loads the images in the given directory
    :param dir: the directory that holds the images
    :return: a list with all the images in the directory
    """
    frames = []
    images_path = sorted_alphanumeric(os.listdir(dir))
    for im_path in images_path:
        if im_path == '.DS_Store':
            continue
        frames.append(cv2.imread(dir + '/' + im_path))
    return frames


def compute_homographies(frames, translation_only):
    """
    Computes the homography between every two consecutive frames in the given list of frames
    :param frames: a list with frames for which the homographies should be calculated
    :param translation_only: indicates if the motion in the sequence is a pure translation motion
    :return: an ndarray of shape 3x3xlen(frames) holding all homographies between consecutive frames.
            homographies[:,:,i] is the 3x3 homography between the frames i and i+1
    """
    num_frames = len(frames)
    homographies = np.zeros((3, 3, num_frames - 1))
    for i in range(num_frames - 1):
        homographies[:, :, i] = Homography(frames[i], frames[i + 1], translation_only=translation_only)
    return homographies


def Homography(img1, img2, selection_area=None, translation_only=False):
    """
    Computes the homography between the two given images.
    :param img1: The first image
    :param img2: The second image
    :param selection_area: Specifies the area on which to focus for computing the homography. Allows to calculate the
            homography between two images according to a selected object in the image and not the global motion.
    :param translation_only: A flag indicating if the input sequence is a pure translation sequence. If True, the
            2x2 rotation part of the homography will be the identity matrix
    :return: A 3x3 matrix, representing the homography between the two given frames.
    """
    if img2 is None:
        return
    orb = cv2.ORB_create()

    # use mask:
    if selection_area:
        prev_mask = np.zeros_like(img2[:, :, 0])
        prev_mask[selection_area[0]:selection_area[1], selection_area[2]:selection_area[3]] = 255
        kpt1, des1 = orb.detectAndCompute(img2, prev_mask)
        kpt2, des2 = orb.detectAndCompute(img1, prev_mask)

    else:
        kpt1, des1 = orb.detectAndCompute(img2, None)
        kpt2, des2 = orb.detectAndCompute(img1, None)

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    matches = sorted(matches, key=lambda x: x.distance)

    src_pts = np.float32([kpt1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kpt2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

    if selection_area:
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    else:
        M, inliers = ransac_homography(src_pts[:, 0, :], dst_pts[:, 0, :], 100, 6, translation_only)

    return M


def ransac_homography(points1, points2, num_iter, inlier_tol, translation_only=False):
    """
    Computes homography between two sets of points using RANSAC.
    :param pos1: An array with shape (N,2) containing N rows of [x,y] coordinates of matched points in image 1.
    :param pos2: An array with shape (N,2) containing N rows of [x,y] coordinates of matched points in image 2.
    :param num_iter: Number of RANSAC iterations to perform.
    :param inlier_tol: inlier tolerance threshold.
    :param translation_only: see estimate rigid transform
    :return: A list containing:
            1) A 3x3 normalized homography matrix.
            2) An Array with shape (S,) where S is the number of inliers,
            containing the indices in pos1/pos2 of the maximal set of inlier matches found.
    """
    N = points1.shape[0]
    largest_inlier_set = []
    for iter in range(num_iter):
        if translation_only: # if True only 1 point should be sampled
            J = np.random.choice(np.arange(N), 1)
        else: # transformation is rigid, so 2 distinct points are required
            J = np.random.choice(np.arange(N), 2, replace=False)
        p1_J = points1[J]
        p2_J = points2[J]
        H12 = estimate_rigid_transform(p1_J, p2_J, translation_only)
        transformed_points2 = apply_homography(points1, H12)
        E = np.power(np.linalg.norm(transformed_points2 - points2, axis=1), 2)
        current_inlier_set = np.where(E < inlier_tol)[0]
        if len(current_inlier_set) > len(largest_inlier_set):
            largest_inlier_set = current_inlier_set
    p1_inliers = points1[largest_inlier_set]
    p2_inliers = points2[largest_inlier_set]
    final_H12 = estimate_rigid_transform(p1_inliers, p2_inliers, translation_only)
    return [final_H12, largest_inlier_set]


def apply_homography(pos1, H12):
    """
    Apply homography to inhomogenous points.
    :param pos1: An array with shape (N,2) of [x,y] point coordinates.
    :param H12: A 3x3 homography matrix.
    :return: An array with the same shape as pos1 with [x,y] point coordinates obtained from transforming pos1 using H12.
    """
    N = pos1.shape[0]
    z_coor = np.ones((N, 1))
    polar_rep = np.concatenate((pos1, z_coor), axis=1)
    tilda_points = np.matmul(H12, polar_rep.T)
    transform_points = np.zeros((2, N))
    transform_points[0] = tilda_points[0] / tilda_points[2]
    transform_points[1] = tilda_points[1] / tilda_points[2]
    return transform_points.T


def estimate_rigid_transform(points1, points2, translation_only=False):
    """
    Computes rigid transforming points1 towards points2, using least squares method.
    points1[i,:] corresponds to poins2[i,:]. In every point, the first coordinate is *x*.
    :param points1: array with shape (N,2). Holds coordinates of corresponding points from image 1.
    :param points2: array with shape (N,2). Holds coordinates of corresponding points from image 2.
    :param translation_only: whether to compute translation only. False (default) to compute rotation as well.
    :return: A 3x3 array with the computed homography.
    """
    centroid1 = points1.mean(axis=0)
    centroid2 = points2.mean(axis=0)
    if translation_only:
        rotation = np.eye(2)
        translation = centroid2 - centroid1
    else:
        centered_points1 = points1 - centroid1
        centered_points2 = points2 - centroid2
        sigma = centered_points2.T @ centered_points1
        # sigma = np.matmul(centered_points2.T, centered_points1)
        U, _, Vt = np.linalg.svd(sigma)
        rotation = U @ Vt
        translation = -rotation @ centroid1 + centroid2
    H = np.eye(3)
    H[:2, :2] = rotation
    H[:2, 2] = translation
    return H


def accumulate_homographies(H_succesive, m):
    if H_succesive is None:
        raise Exception("Please press 'Compute Motion' first!")
    M = H_succesive.shape[2] + 1
    H2m = np.zeros((3, 3, M))
    H2m[:, :, m] = np.eye(3)
    for i in reversed(range(m)):
        H2m[:, :, i] = np.dot(H2m[:, :, i + 1], H_succesive[:, :, i])
        H2m[:, :, i] /= H2m[2, 2, i]
    for i in range(m, M-1):
        H2m[:, :, i+1] = np.dot(H2m[:, :, i], np.linalg.inv(H_succesive[:, :, i]))
        H2m[:, :, i+1] /= H2m[2, 2, i+1]
    return H2m


def BGR2RGB(image):
    return image[:, :, ::-1]


def sorted_alphanumeric(data):
    import re
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    return sorted(data, key=alphanum_key)


class MousePositionTracker(tk.Frame):
    """ Tkinter Canvas mouse position widget. """

    def __init__(self, canvas):
        self.canvas = canvas
        self.canv_width = self.canvas.cget('width')
        self.canv_height = self.canvas.cget('height')
        self.reset()

        # Create canvas cross-hair lines.
        xhair_opts = dict(dash=(3, 2), fill='white', state=tk.HIDDEN)
        self.lines = (self.canvas.create_line(0, 0, 0, self.canv_height, **xhair_opts),
                      self.canvas.create_line(0, 0, self.canv_width,  0, **xhair_opts))

    def cur_selection(self):
        return (self.start, self.end)

    def begin(self, event):
        self.hide()
        self.start = (event.x, event.y)  # Remember position (no drawing).

    def update(self, event):
        self.end = (event.x, event.y)
        self._update(event)
        self._command(self.start, (event.x, event.y))  # User callback.

    def _update(self, event):
        # Update cross-hair lines.
        self.canvas.coords(self.lines[0], event.x, 0, event.x, self.canv_height)
        self.canvas.coords(self.lines[1], 0, event.y, self.canv_width, event.y)
        self.show()

    def reset(self):
        self.start = self.end = None

    def hide(self):
        self.canvas.itemconfigure(self.lines[0], state=tk.HIDDEN)
        self.canvas.itemconfigure(self.lines[1], state=tk.HIDDEN)

    def show(self):
        self.canvas.itemconfigure(self.lines[0], state=tk.NORMAL)
        self.canvas.itemconfigure(self.lines[1], state=tk.NORMAL)

    def autodraw(self, command=lambda *args: None):
        """Setup automatic drawing; supports command option"""
        self.reset()
        self._command = command
        self.canvas.bind("<Button-1>", self.begin)
        self.canvas.bind("<B1-Motion>", self.update)
        self.canvas.bind("<ButtonRelease-1>", self.quit)

    def quit(self, event):
        self.hide()  # Hide cross-hairs.
        # self.reset()


class SelectionObject:
    """ Widget to display a rectangular area on given canvas defined by two points
        representing its diagonal.
    """
    def __init__(self, canvas, select_opts):
        # Create a selection objects for updating.
        self.canvas = canvas
        self.select_opts1 = select_opts
        self.width = self.canvas.cget('width')
        self.height = self.canvas.cget('height')

        # Options for areas outside rectanglar selection.
        select_opts1 = self.select_opts1.copy()
        select_opts1.update({'state': tk.HIDDEN})  # Hide initially.
        # Separate options for area inside rectanglar selection.
        select_opts2 = dict(dash=(2, 2), fill='', outline='white', state=tk.HIDDEN)

        # Initial extrema of inner and outer rectangles.
        imin_x, imin_y,  imax_x, imax_y = 0, 0,  1, 1
        omin_x, omin_y,  omax_x, omax_y = 0, 0,  self.width, self.height

        self.rects = (
            # Area outside selection (inner) rectangle.
            self.canvas.create_rectangle(omin_x, omin_y,  omax_x, imin_y, **select_opts1),
            self.canvas.create_rectangle(omin_x, imin_y,  imin_x, imax_y, **select_opts1),
            self.canvas.create_rectangle(imax_x, imin_y,  omax_x, imax_y, **select_opts1),
            self.canvas.create_rectangle(omin_x, imax_y,  omax_x, omax_y, **select_opts1),
            # Inner rectangle.
            self.canvas.create_rectangle(imin_x, imin_y,  imax_x, imax_y, **select_opts2)
        )

    def update(self, start, end):
        # Current extrema of inner and outer rectangles.
        imin_x, imin_y,  imax_x, imax_y = self._get_coords(start, end)
        omin_x, omin_y,  omax_x, omax_y = 0, 0,  self.width, self.height

        # Update coords of all rectangles based on these extrema.
        self.canvas.coords(self.rects[0], omin_x, omin_y,  omax_x, imin_y),
        self.canvas.coords(self.rects[1], omin_x, imin_y,  imin_x, imax_y),
        self.canvas.coords(self.rects[2], imax_x, imin_y,  omax_x, imax_y),
        self.canvas.coords(self.rects[3], omin_x, imax_y,  omax_x, omax_y),
        self.canvas.coords(self.rects[4], imin_x, imin_y,  imax_x, imax_y),

        for rect in self.rects:  # Make sure all are now visible.
            self.canvas.itemconfigure(rect, state=tk.NORMAL)

    def _get_coords(self, start, end):
        """ Determine coords of a polygon defined by the start and
            end points one of the diagonals of a rectangular area.
        """
        return (min((start[0], end[0])), min((start[1], end[1])),
                max((start[0], end[0])), max((start[1], end[1])))

    def hide(self):
        for rect in self.rects:
            self.canvas.itemconfigure(rect, state=tk.HIDDEN)


class Application(tk.Frame):

    # Default selection object options.
    SELECT_OPTS = dict(dash=(5, 5), stipple='gray25', outline='')  # fill="white"

    def __init__(self, root, parent, path, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        # all_files = sorted(os.listdir(root.directory))
        # path = root.directory + '/' + all_files[len(all_files)//2]
        # path = root.directory + '/Lego133.jpg'
        # print(path)
        img = ImageTk.PhotoImage(Image.open(path))
        self.canvas = tk.Canvas(parent, width=img.width(), height=img.height(),
                                borderwidth=0, highlightthickness=0)
        self.canvas.pack(expand=True)

        self.canvas.create_image(0, 0, image=img, anchor=tk.NW)
        self.canvas.img = img  # Keep reference.

        # Create selection object to show current selection boundaries.
        self.selection_obj = SelectionObject(self.canvas, self.SELECT_OPTS)

        # Callback function to update it given two points of its diagonal.
        def on_drag(start, end, **kwarg):  # Must accept these arguments.
            self.selection_obj.update(start, end)
            # print(self.posn_tracker.start)
            # print(self.posn_tracker.end)

        # Create mouse position tracker that uses the function.
        self.posn_tracker = MousePositionTracker(self.canvas)
        self.posn_tracker.autodraw(command=on_drag)  # Enable callbacks.
        # print(self.posn_tracker.start)
        # print(self.posn_tracker.end)


