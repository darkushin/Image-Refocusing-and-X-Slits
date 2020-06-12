import copy
from tkinter import filedialog
from Code.GUI_helper import *


# TODO's:
#  1. Allow the user to select specific frame range (important in the case of apples)
#  3. Display to the user different error messages
#  4. Check that right to left motion works!
#  5. Create all the repos that are necessary for the program when running for the first time (Motion/Results etc.)


class GUI(tk.Frame):
    """
    The main class of the program. This class is responsible for all the GUI logic and execution.
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.directory = ''
        self.file_name = ''
        self.num_frames = 0
        self.im_shape = None
        self.ref_frame = 0
        self.frames = []
        self.homographies = None
        self.warped_im = None
        self.refocused_im = None
        self.dx = 0
        self.dy = 0
        self.selection_area = [0, 0, 0, 0]
        self.current_im_label = None
        self.load_label = None
        self.select_folder_button()
        self.motion_button()
        self.translation_only_checkbutton()
        self.change_focus_button()
        self.select_area_button()
        self.median_mean_radiobutton()
        self.show_button()

    def reset_fields(self):
        """
        Resets all the fields to the initial values. This function is called when the user loads a new folder
        """
        self.directory = ''
        self.file_name = ''
        self.num_frames = 0
        self.ref_frame = 0
        self.im_shape = None
        self.frames = []
        self.homographies = None
        self.warped_im = None
        self.refocused_im = None
        self.selection_area = [0, 0, 0, 0]
        self.dx = 0
        self.dy = 0
        self.translation_only_checkbutton()
        try:
            self.current_im_label.destroy()
        except AttributeError:
            pass

    def select_folder_button(self):
        """
        Displays to the user the 'Select Folder' button which allows the user to select a sequence from the data
        """
        self.add_label(text='Select images folder:', place=[15, 10])
        self.add_button(text="Select Folder", fg="black", command=self.load_dir, place=[15, 30])

    def motion_button(self):
        """
        Displays the 'Compute Motion' button and executes the compute motion function when the user presses the button.
        """
        self.add_label(text='Press the button to calculate the motion between frames:', place=[15, 70])
        self.add_button(text='Compute Motion', place=[15, 90], command=self.compute_motion)

    def translation_only_checkbutton(self):
        """
        Displays to the user the translation only checkbutton which allows the user to indicate that the motion in the
        current sequence is a pure translation without rotation.
        """
        self.trans_only_var = IntVar()
        trans_only_button = Checkbutton(self, text="Translation-Only", variable=self.trans_only_var, onvalue=1,
                                        offvalue=0, height=1, width=14)
        trans_only_button.pack()
        trans_only_button.place(x=180, y=93)

    def select_area_button(self):
        """
        Displays the 'Select Area' button and executes the select area function when the user presses the button.
        """
        self.add_label(text='Press the button to select the focus area:', place=[15, 230])
        self.add_button(text='Select Area', place=[15, 250], command=self.select_area)

    def change_focus_button(self):
        """
        Displays to the user the '+' and '-' buttons to change the motion in both x and y directions. When pressing one
        of these buttons the update_focus_command is being executed to updated the motion in the relevant direction.
        """
        self.add_label(text='Use the buttons below to change the focus:', place=[15, 130])

        self.add_label(text='Left-Right', place=[65, 150])
        self.add_button(text='-', place=[65, 170], command=lambda a='x', b=-0.5: self.update_focus_command(a, b))
        self.add_button(text='+', place=[98, 170], command=lambda a='x', b=0.5: self.update_focus_command(a, b))
        self.x_entry = self.add_entry(place=[75, 195], width=4)

        self.add_label(text='Up-Down', place=[170, 150])
        self.add_button(text='-', place=[168, 170], command=lambda a='y', b=-0.5: self.update_focus_command(a, b))
        self.add_button(text='+', place=[201, 170], command=lambda a='y', b=0.5: self.update_focus_command(a, b))
        self.y_entry = self.add_entry(place=[178, 195], width=4)

    def update_focus_command(self, parameter: str, amount: float = 1):
        """
        Updates the motion in the relevant axis according to the button the user pressed
        :param parameter: 'x' or 'y' representing a desired change in dx or dy respectively
        :param amount: how much pixels to shift in the given direction
        """
        if parameter == 'x':
            self.dx += amount
        if parameter == 'y':
            self.dy += amount

    def median_mean_radiobutton(self):
        """
        Allows the user to select if a mean or a median of all the frames should be computed as the refocused image.
        """
        self.med_mean_var = IntVar()
        median_radiobutton = Radiobutton(self, text="Median", variable=self.med_mean_var, value=1)
        median_radiobutton.pack()
        median_radiobutton.place(x=160, y=290)
        mean_radiobutton = Radiobutton(self, text="Mean (default)", variable=self.med_mean_var, value=2)
        mean_radiobutton.pack()
        mean_radiobutton.place(x=260, y=290)

    def show_button(self):
        """
        Displays the 'Show' button to the user. When pressing this button the refocused image, according to the
        different parameters the user defined is being computed.
        """
        self.add_button(text='Show', place=[200, 320], command=self.display_result)

    def display_result(self):
        """
        Calculates the refocused image according to the changes made by the user and displays the result to the user in
        a new window.
        """
        try:
            if not self.frames:
                raise UserError('Please load a sequence first and then press the Compute Motion button')
            if self.homographies is None:
                raise UserError('Please compute the motion between frames first!')

            try:
                self.current_im_label.destroy()
            except AttributeError:
                pass

            # Check that the images are aligned. If not, align the images
            if self.warped_im is None:
                self.align_images()

            # Update the translation according to the values the user filled
            self.update_focus_parameters()
            self.refocus_im()

            # Use either mean or median for the refocused image, according to the user's selection
            if self.med_mean_var.get() == 1:
                refocused_im = np.median(self.refocused_im, axis=3).astype(np.uint8)
            else:
                refocused_im = np.mean(self.refocused_im, axis=3).astype(np.uint8)

            # display the image to the user in a new window
            window = Toplevel(root)
            window.title('Refocused Image')
            img = ImageTk.PhotoImage(Image.fromarray(BGR2RGB(refocused_im)))
            canvas = tk.Canvas(window, width=img.width(), height=img.height(),
                                    borderwidth=0, highlightthickness=0)
            canvas.pack(expand=True)
            canvas.create_image(0, 0, image=img, anchor=tk.NW)
            canvas.img = img
            label_text = f'Current refocused image:\ndx={self.dx}\ndy={self.dy}'
            self.current_im_label = self.add_label(text=label_text, place=[320, 220], borderwidth=2)

        except Exception as e:
            display_error(root, 'Error occurred while refocusing the image. Error: ' + e.args[0])

    def refocus_im(self):
        """
        Computes the refocused image according to the translation the user defined in both axes.
        """
        if self.dx == 0 and self.dy == 0:
            self.refocused_im = copy.deepcopy(self.warped_im)
        else:
            for i in range(self.num_frames):
                self.refocused_im[:, :, :, i] = create_translated_im(self.warped_im[:, :, :, i], dx=self.dx * (i + 1),
                                                                     dy=self.dy * (i + 1))

    def update_focus_parameters(self):
        """
        Checks if the user inserted values in the motion entries, and updates the relevant parameters accordingly
        """
        if self.x_entry.get():
            self.dx = float(self.x_entry.get())
            self.x_entry.delete(0, 'end')
        if self.y_entry.get():
            self.dy = float(self.y_entry.get())
            self.y_entry.delete(0, 'end')

    def align_images(self):
        """
        Aligns all images in the sequence with respect to the reference frame
        """
        self.warped_im = np.zeros(self.im_shape + (self.num_frames,))

        # compute the accumulate homographies of each frame with respect to the reference frame
        accum_homographies = accumulate_homographies(self.homographies, self.ref_frame)

        # warp images according to homographies:
        for i in range(self.num_frames):
            h_inv = np.linalg.inv(accum_homographies[:, :, i])
            self.warped_im[:, :, :, i] = cv2.warpPerspective(self.frames[i], h_inv,
                                                             (self.im_shape[1], self.im_shape[0]))
        self.refocused_im = copy.deepcopy(self.warped_im)

    def load_dir(self):
        """
        Loads the dir the user selected and displays the number of frames in it and the size of an image
        """
        try:
            try:
                self.load_label.destroy()
            except AttributeError:
                pass
            self.reset_fields()
            self.directory = filedialog.askdirectory(initialdir="/", title="select dir") + '/'
            self.file_name = self.directory.split('/')[-2]

            # load frames:
            self.frames = load_images(self.directory)
            if self.frames:
                self.num_frames = len(self.frames)
                self.im_shape = self.frames[0].shape
                self.load_label = self.add_label(text=f'Folder Name: {self.file_name}\n'
                                                      f'Number of Frames: {len(self.frames)}\n'
                                                      f'Frame size: {self.im_shape[0]}x{self.im_shape[1]}',
                                                 place=[200, 10])
                self.ref_frame = self.num_frames // 2 - 1

        except AttributeError as e:
            display_error(root, 'Error while loading the folder. Make sure you selected the correct folder and that it '
                                'contains images')
        except Exception as e:
            display_error(root, 'Error occurred while loading folder. Error: ' + e.args[0])

    def compute_motion(self):
        """
        Calculates the motion between every two consecutive frames in the sequence and saves it in a file
        '/Motion/<sequence_name>.csv'. If the file already exists, it loads this file instead of recomputing the motion.
        """
        try:
            if not self.directory:
                raise UserError('Please load a folder first!')
            self.homographies = np.genfromtxt('../Motion/' + self.file_name + '.csv', delimiter=',') \
                .reshape((3, 3, self.num_frames - 1))
        except UserError as e:  # catch the error if the user didn't load a folder
            display_error(root, e.message)

        except IOError:  # no motion file exists - catch the IOError, calculate and save the motion
            self.homographies = np.zeros((3, 3, self.num_frames - 1))
            for i in range(self.num_frames - 1):
                self.homographies[:, :, i] = Homography(self.frames[i], self.frames[i + 1],
                                                        translation_only=self.trans_only_var.get())
            csv_data = self.homographies.reshape((9, self.num_frames - 1))
            np.savetxt('../Motion/' + self.file_name + '.csv', csv_data, delimiter=',')

        except Exception as e:
            display_error(root, 'Error occurred while computing motion. Error: ' + e.args[0])

    def select_area(self):
        """
        Allows the user to specify the area of focus.
        """
        BACKGROUND = 'grey'
        TITLE = 'Image Cropper'

        window = Toplevel(root)
        window.title(TITLE)
        window.configure(background=BACKGROUND)

        # todo: change this if I allow to choose the reference frame
        print(len(self.frames))
        select_window = Application(root, window, self.frames[self.ref_frame], background=BACKGROUND)
        select_window.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.TRUE)
        done_button = tk.Button(select_window, text='Done', fg='black',
                                command=lambda a=window, b=select_window: self.done_selecting(a, b))
        done_button.pack()
        select_window.mainloop()

    def done_selecting(self, window, select_window):
        try:
            try:
                self.current_im_label.destroy()
            except AttributeError:
                pass
            self.selection_area[0] = min(select_window.posn_tracker.start[1], select_window.posn_tracker.end[1])
            self.selection_area[1] = max(select_window.posn_tracker.start[1], select_window.posn_tracker.end[1])
            self.selection_area[2] = min(select_window.posn_tracker.start[0], select_window.posn_tracker.end[0])
            self.selection_area[3] = max(select_window.posn_tracker.start[0], select_window.posn_tracker.end[0])
            window.destroy()

            # Calculate homography of every frame with ref frame
            self.homographies = np.zeros((3, 3, self.num_frames))
            for i in range(self.num_frames):
                self.homographies[:, :, i] = Homography(self.frames[i], self.frames[self.ref_frame],
                                                        selection_area=self.selection_area,
                                                        translation_only=self.trans_only_var.get())

            # Warp images according to homographies:
            warped_frames = np.zeros(self.frames[self.ref_frame].shape + (self.num_frames,))
            for i in range(self.num_frames):
                h_inv = np.linalg.inv(self.homographies[:, :, i])
                warped_frames[:, :, :, i] = cv2.warpPerspective(self.frames[i], h_inv,
                                                                (self.frames[self.ref_frame].shape[1],
                                                                 self.frames[self.ref_frame].shape[0]))

            # Use either mean or median for the refocused image, according to the user's selection
            if self.med_mean_var.get() == 1:
                refocused_im = np.median(warped_frames, axis=3).astype(np.uint8)
            else:
                refocused_im = np.mean(warped_frames, axis=3).astype(np.uint8)

            # display the image to the user in a new window
            window = Toplevel(root)
            window.title('Refocused Image')
            img = ImageTk.PhotoImage(Image.fromarray(BGR2RGB(refocused_im)))
            canvas = tk.Canvas(window, width=img.width(), height=img.height(),
                                    borderwidth=0, highlightthickness=0)
            canvas.pack(expand=True)
            canvas.create_image(0, 0, image=img, anchor=tk.NW)
            canvas.img = img
        except ValueError:
            display_error(root, 'Not enough feature points in the selected area. Please select a larger area')
        self.selection_area = [0, 0, 0, 0]

    def add_label(self, text: str, place: list, borderwidth: int = 0):
        """
        Adds a label with the given text in the given location to the GUI
        """
        if borderwidth:
            label = tk.Label(self, text=text, borderwidth=borderwidth, relief='ridge')
        else:
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
    os.system(f'mkdir ../Motion')

    WIDTH, HEIGHT = 500, 350
    BACKGROUND = 'grey'
    TITLE = 'Refocusing GUI'

    root = tk.Tk()
    root.title(TITLE)
    root.geometry('%sx%s' % (WIDTH, HEIGHT))

    gui = GUI(root)
    gui.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.TRUE)
    gui.mainloop()
