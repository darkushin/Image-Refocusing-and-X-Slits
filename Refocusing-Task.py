from tkinter import filedialog
from tkinter import *
import tkinter as tk
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from os import listdir
import numpy as np
from GUI_helper import *


# TODO's:
#  1. Allow the user to select specific frame range (important in the case of apples)
#  2. Change the displayed image to tkinter and not cv2.imshow()
#  3. Display to the user different error messages
#  4. Check that right to left motion works!

# delete .DS_Store files:
# open terminal and go to the desired sequence and type: find . -name '.DS_Store' -type f -delete


class GUI(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.directory = ''
        self.file_name = ''
        self.num_frames = 0
        self.ref_frame = 0
        self.frames = []
        self.homographies = None
        self.accum_h = None
        self.images_path = []
        self.selection_area = [0, 0, 0, 0]
        self.select_folder_button()
        self.motion_button()
        self.translation_only_checkbutton()
        self.change_focus_button()
        self.select_area_button()
        self.median_mean_radiobutton()
        self.show_button()

    def reset_fields(self):
        self.directory = ''
        self.file_name = ''
        self.num_frames = 0
        self.ref_frame = 0
        self.frames = []
        self.homographies = None
        self.accum_h = None
        self.images_path = []
        self.selection_area = [0, 0, 0, 0]

    def select_folder_button(self):
        self.add_label(text='Select images folder:', place=[15, 10])
        self.add_button(text="Select Folder", fg="black", command=self.load_dir, place=[15, 30])

    def motion_button(self):
        """
        Displays the 'Compute Motion' button, and executes the compute motion function when the user presses the button.
        """
        self.add_label(text='Press the button to calculate the motion between frames:', place=[15, 70])
        self.add_button(text='Compute Motion', place=[15, 90], command=self.compute_motion)

    def translation_only_checkbutton(self):
        self.trans_only_var = IntVar()
        trans_only_button = Checkbutton(self, text="Translation-Only", variable=self.trans_only_var, onvalue=1,
                                        offvalue=0, height=1, width=14)
        trans_only_button.pack()
        trans_only_button.place(x=180, y=93)

    def select_area_button(self):
        """
        Displays the 'Select Area' button, and executes the select area function when the user presses the button.
        """
        self.add_label(text='Press the button to select the focus area:', place=[15, 230])
        self.add_button(text='Select Area', place=[15, 250], command=self.select_area)

    def change_focus_button(self):
        """
        Displays the 'Select Area' button, and executes the select area function when the user presses the button.
        """
        self.add_label(text='Use the buttons below to change the focus:', place=[15, 130])

        self.add_label(text='Left-Right', place=[15, 150])
        self.add_button(text='-', place=[15, 170], command=lambda a='x', b=-1: self.update_focus_command(a, b))
        self.add_button(text='+', place=[48, 170], command=lambda a='x': self.update_focus_command(a))
        self.x_entry = self.add_entry(place=[25, 195], width=4)

        self.add_label(text='Up-Down', place=[120, 150])
        self.add_button(text='-', place=[118, 170], command=lambda a='y', b=-1: self.update_focus_command(a, b))
        self.add_button(text='+', place=[151, 170], command=lambda a='y': self.update_focus_command(a))
        self.y_entry = self.add_entry(place=[128, 195], width=4)

        self.add_label(text='Rotate', place=[225, 150])
        self.add_button(text='-', place=[212, 170])
        self.add_button(text='+', place=[245, 170])
        self.alpha_entry = self.add_entry(place=[222, 195], width=4)

    def update_focus_command(self, parameter: str, amount: float = 1):
        if self.accum_h is None:
            self.accum_h = accumulate_homographies(self.homographies, self.ref_frame)
        if parameter == 'x':  # update dx in the homography
            self.accum_h[0, 2, :self.ref_frame] += amount
            self.accum_h[0, 2, self.ref_frame + 1:] -= amount
        elif parameter == 'y':  # update dy in the homography
            self.accum_h[1, 2, :self.ref_frame] += amount
            self.accum_h[1, 2, self.ref_frame + 1:] -= amount
        else:  # update the rotation matrix in the homography
            alpha_rad = amount * np.pi / 180
            self.accum_h[0, 0, :self.ref_frame] += np.cos(alpha_rad)
            self.accum_h[1, 1, :self.ref_frame] += np.cos(alpha_rad)
            self.accum_h[0, 1, :self.ref_frame] += -np.sin(alpha_rad)
            self.accum_h[1, 0, :self.ref_frame] += np.sin(alpha_rad)
            self.accum_h[0, 0, self.ref_frame + 1:] -= np.cos(alpha_rad)
            self.accum_h[1, 1, self.ref_frame + 1:] -= np.cos(alpha_rad)
            self.accum_h[0, 1, self.ref_frame + 1:] -= -np.sin(alpha_rad)
            self.accum_h[1, 0, self.ref_frame + 1:] -= np.sin(alpha_rad)

    def median_mean_radiobutton(self):
        self.med_mean_var = IntVar()
        median_radiobutton = Radiobutton(self, text="Median", variable=self.med_mean_var, value=1)
        median_radiobutton.pack()
        median_radiobutton.place(x=160, y=290)
        mean_radiobutton = Radiobutton(self, text="Mean", variable=self.med_mean_var, value=2)
        mean_radiobutton.pack()
        mean_radiobutton.place(x=260, y=290)

    def show_button(self):
        self.add_button(text='Show', place=[200, 320], command=self.display_result)

    def display_result(self):
        if self.accum_h is None:
            self.accum_h = accumulate_homographies(self.homographies, self.ref_frame)
        if self.x_entry.get():
            self.update_focus_command('x', amount=float(self.x_entry.get()))
            self.x_entry.delete(0, 'end')
        if self.y_entry.get():
            self.update_focus_command('y', amount=float(self.y_entry.get()))
            self.y_entry.delete(0, 'end')
        if self.alpha_entry.get():
            self.update_focus_command('alpha', amount=float(self.alpha_entry.get()))
            self.alpha_entry.delete(0, 'end')

        print(self.accum_h[:, :, 0])

        # warp the images according to accum_h:
        shape = self.frames[0].shape + (self.num_frames,)
        warped_im = np.zeros(shape)
        for i in range(self.num_frames):
            warped_im[:, :, :, i] = cv2.warpPerspective(self.frames[i], np.linalg.inv(self.accum_h[:, :, i]),
                                                        (self.frames[0].shape[1], self.frames[0].shape[0]))

        if self.med_mean_var.get() == 2:
            print("using mean")
            refocused_im = np.mean(warped_im, axis=3)
        else:
            print("using median")
            refocused_im = np.median(warped_im, axis=3)
        refocused_im = (refocused_im - np.min(refocused_im)) / (np.max(refocused_im) - np.min(refocused_im))

        cv2.imshow('refocused_im', refocused_im)
        cv2.waitKey(0)

    def load_dir(self):
        """
        Loads the dir the user selected and displays the number of frames in it and the size of an image
        """
        try:
            self.load_label.destroy()
        except AttributeError:
            pass
        self.reset_fields()
        # todo: add try and accept for cases where there are other things in the folder than images
        self.directory = filedialog.askdirectory(initialdir="/", title="select dir") + '/'
        self.file_name = self.directory.split('/')[-2]
        print(self.directory)

        # load frames:
        self.images_path = sorted_alphanumeric(os.listdir(self.directory))
        for im_path in self.images_path:
            self.frames.append(cv2.imread(self.directory + im_path))

        if self.frames:
            self.num_frames = len(self.frames)
            self.load_label = self.add_label(text=f'Folder Name: {self.file_name}\n'
                                                  f'Number of Frames: {len(self.frames)}\n'
                                                  f'Frame size: {self.frames[0].shape[0]}x{self.frames[0].shape[1]}',
                                             place=[200, 10])
            self.ref_frame = self.num_frames // 2 - 1
        else:
            print("error")
            # todo: display to the user an error message that the folder is empty

    def compute_motion(self):
        """
        Calculates the motion between every two consecutive frames in the sequence and saves it in a file
        '/Motion/<sequence_name>.csv'. If the file already exists, it loads this file instead of recomputing the motion.
        """
        try:
            self.homographies = np.genfromtxt('Motion/' + self.file_name + '.csv', delimiter=',') \
                .reshape((3, 3, self.num_frames - 1))
        except Exception as e:
            self.homographies = np.zeros((3, 3, self.num_frames - 1))
            for i in range(self.num_frames - 1):
                self.homographies[:, :, i] = Homography(self.frames[i], self.frames[i + 1],
                                                        translation_only=self.trans_only_var.get())
            csv_data = self.homographies.reshape((9, self.num_frames - 1))
            np.savetxt('Motion/' + self.file_name + '.csv', csv_data, delimiter=',')

    def select_area(self):
        """
        Allows the user to specify the area of focus.
        """
        BACKGROUND = 'grey'
        TITLE = 'Image Cropper'

        window = Toplevel(root)
        window.title(TITLE)
        # window.geometry('%sx%s' % (WIDTH, HEIGHT))
        window.configure(background=BACKGROUND)

        # todo: change this if I allow to choose the reference frame
        print(len(self.frames))
        ref_path = self.directory + self.images_path[self.ref_frame]  # the path to the reference frame
        select_window = Application(root, window, ref_path, background=BACKGROUND)
        select_window.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.TRUE)
        done_button = tk.Button(select_window, text='Done', fg='black',
                                command=lambda a=window, b=select_window: self.done_selecting(a, b))
        done_button.pack()
        select_window.mainloop()

    def done_selecting(self, window, select_window):
        print(select_window.posn_tracker.start)
        print(select_window.posn_tracker.end)
        self.selection_area[0] = min(select_window.posn_tracker.start[1], select_window.posn_tracker.end[1])
        self.selection_area[1] = max(select_window.posn_tracker.start[1], select_window.posn_tracker.end[1])
        self.selection_area[2] = min(select_window.posn_tracker.start[0], select_window.posn_tracker.end[0])
        self.selection_area[3] = max(select_window.posn_tracker.start[0], select_window.posn_tracker.end[0])
        window.destroy()

        ref_frame = (self.num_frames // 2) - 1
        # Calculate homography of every frame with ref frame
        self.homographies = np.zeros((3, 3, self.num_frames))
        for i in range(self.num_frames):
            self.homographies[:, :, i] = Homography(self.frames[i], self.frames[ref_frame],
                                                    selection_area=self.selection_area)
        # warp images according to homographies:
        ref_color = [np.mean(self.frames[ref_frame][:, :, i]) for i in range(3)]
        warped_frames = np.zeros(self.frames[ref_frame].shape + (self.num_frames,))
        for i in range(self.num_frames):
            h_inv = np.linalg.inv(self.homographies[:, :, i])
            warped_frames[:, :, :, i] = cv2.warpPerspective(self.frames[i], h_inv,
                                                            (self.frames[ref_frame].shape[1],
                                                             self.frames[ref_frame].shape[0]))
            mask = warped_frames[:, :, :, i] == [0, 0, 0]
            warped_frames[:, :, :, i][mask] = ref_color[0]
            warped_frames[:, :, :, i][mask] = ref_color[1]
            warped_frames[:, :, :, i][mask] = ref_color[2]
        averaged_im = np.median(warped_frames, axis=3)
        averaged_im = (averaged_im - np.min(averaged_im)) / (np.max(averaged_im) - np.min(averaged_im))
        cv2.imshow('average_im', averaged_im)
        cv2.waitKey(0)

        self.selection_area = [0, 0, 0, 0]

    def add_label(self, text: str, place: list):
        """
        Adds a label with the given text in the given location to the GUI
        """
        label = tk.Label(self, text=text)
        label.pack()
        label.place(x=place[0], y=place[1])
        return label

    def add_button(self, text: str, place: list, fg: str = 'black', command=None):
        """
        Adds a button with the given text in the given location to the GUI
        """
        button = tk.Button(self, text=text, fg=fg, command=command)
        button.pack()
        button.place(x=place[0], y=place[1])

    def add_entry(self, place: list, width=20):
        """
        Adds an entry for allowing the user to insert text in the given location in the GUI.
        """
        entry = tk.Entry(self, width=width)
        entry.pack()
        entry.place(x=place[0], y=place[1])
        return entry


if __name__ == '__main__':
    WIDTH, HEIGHT = 500, 350
    BACKGROUND = 'grey'
    TITLE = 'Refocusing GUI'

    root = tk.Tk()
    root.title(TITLE)
    root.geometry('%sx%s' % (WIDTH, HEIGHT))
    # root.configure(background=BACKGROUND)

    gui = GUI(root)  # , background=BACKGROUND)
    gui.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.TRUE)
    gui.mainloop()
