from tkinter import filedialog
from os import listdir
from Code.GUI_helper import *

dirname = os.path.dirname(__file__)


class GUI(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.directory = ''
        self.file_name = ''
        self.frames = []
        self.num_frames = 0
        self.homographies = None
        self.start_frame = 0
        self.end_frame = 0
        self.initial_start_frame = 0
        self.initial_end_frame = 0
        self.start_column = 0
        self.end_column = 1
        self.rotate_angle = 0
        self.im_shape = None
        self.start_frame_entry = None
        self.end_frame_entry = None
        self.start_column_entry = None
        self.end_column_entry = None
        self.move_columns_entry = None
        self.move_frames_entry = None
        self.rotate_slit_entry = None
        self.select_folder_button()
        self.motion_button()
        self.select_slice()
        self.move_slice()
        self.current_slit_label = None
        self.rotate_angle_label = None
        self.add_button(text='Show', place=[200, 360], command=self.create_slit)

    def select_folder_button(self):
        """
        Creates the folder selection label and button in the GUI.
        """
        self.add_label(text='Select images folder:', place=[15, 10])
        self.add_button(text="Select Folder", fg="black", command=self.load_dir, place=[15, 30])

    def motion_button(self):
        """
        Displays the 'Compute Motion' button, and executes the compute motion function when the user presses the button.
        """
        self.add_label(text='Press the button to calculate the motion between frames:', place=[15, 70])
        self.add_button(text='Compute Motion', place=[15, 90], command=self.compute_motion)

    def select_slice(self):
        """
        Allows the user to specify the starting and ending frames and cols that will define the X-Slit slice
        """
        self.add_label(text='Please define the desired slice start and end points:', place=[15, 130])
        self.add_label(text='Frames:      Start       End\tColumns:      Start       End', place=[15, 150])
        self.start_frame_entry = self.add_entry(place=[90, 170], width=3)
        self.end_frame_entry = self.add_entry(place=[147, 170], width=3)
        self.start_column_entry = self.add_entry(place=[315, 170], width=3)
        self.end_column_entry = self.add_entry(place=[372, 170], width=3)

    def move_slice(self):
        """
        Allows the user to move the selected slice, left-right, forward-backward and zoom in-zoom out.
        """
        self.add_label(text='Insert different values to create different space-time volume slices:', place=[15, 230])
        self.add_label(text='Backward-Forward (#frames)', place=[15, 250])
        self.move_frames_entry = self.add_entry(place=[85, 270], width=4)
        self.add_label(text='Left-Right (#pixels)', place=[215, 250])
        self.move_columns_entry = self.add_entry(place=[260, 270], width=4)
        self.add_label(text='Zoom in/out (degree)', place=[350, 250])
        self.rotate_slit_entry = self.add_entry(place=[400, 270], width=4)

    def load_dir(self):
        """
        Loads the dir the user selected and displays the number of frames in it and the size of an image
        """
        try:
            try:
                self.load_label.destroy()
            except AttributeError:
                pass
            self.directory = filedialog.askdirectory(initialdir="/", title="select dir") + '/'
            self.file_name = self.directory.split('/')[-2]
            print(self.directory)

            # load frames:
            self.frames = load_images(self.directory)
            if self.frames:
                self.num_frames = len(self.frames)
                self.im_shape = self.frames[0].shape
                self.load_label = self.add_label(text=f'Folder Name: {self.file_name}\n'
                                                      f'Number of Frames: {len(self.frames)}\n'
                                                      f'Frame size: {self.im_shape[0]}x{self.im_shape[1]}',
                                                 place=[200, 10])
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
            self.validate_motion_direction()

        except UserError as e:  # catch the error if the user didn't load a folder
            display_error(root, e.message)

        except IOError:  # if no motion file for the loaded folder was previously created, catch the IOError,
            # calculate and save the motion
            self.validate_motion_direction()
            self.homographies = np.zeros((3, 3, self.num_frames - 1))
            for i in range(self.num_frames - 1):
                self.homographies[:, :, i] = Homography(self.frames[i], self.frames[i + 1], translation_only=True)
            csv_data = self.homographies.reshape((9, self.num_frames - 1))
            np.savetxt('../Motion/' + self.file_name + '.csv', csv_data, delimiter=',')

        except Exception as e:
            display_error(root, 'Error occurred while computing motion. Error: ' + e.args[0])

    def validate_motion_direction(self):
        """
        Validates that the given sequence is taken from left to right. If the sequence was taken from right to left,
        this function reverses the frames.
        """
        test_num = max(int(len(self.frames) // 10), 1)
        test_homographies = np.zeros((3, 3, test_num))
        for i in range(test_num):
            test_homographies[:, :, i] = Homography(self.frames[i], self.frames[i + 1], translation_only=True)
        if np.sum(test_homographies[0, 2, :]) < 0:
            self.frames = self.frames[::-1]

    def create_slit(self):
        """
        Calculates the panorama slit according to the values specified by the user and saves the image to the user.
        """
        try:
            if self.homographies is None:
                raise UserError('Please compute the motion between frames first!')
            try:
                self.current_slit_label.destroy()
            except AttributeError:
                pass
            panorama_im = self.create_panorama()
            window = Toplevel(root)
            window.title('Panorama Image')
            img = ImageTk.PhotoImage(Image.fromarray(BGR2RGB(panorama_im)))
            canvas = tk.Canvas(window, width=img.width(), height=img.height(),
                               borderwidth=0, highlightthickness=0)
            canvas.pack(expand=True)
            canvas.create_image(0, 0, image=img, anchor=tk.NW)
            canvas.img = img
            label_text = f'Current slit - frames: {self.start_frame}-{self.end_frame}, columns: {self.start_column}-' \
                         f'{self.end_column}'
            self.current_slit_label = self.add_label(text=label_text, place=[100, 330])
        except UserError as e:
            display_error(root, e.message, e.orig_err_msg)
        except Exception as e:
            display_error(root, 'Error occurred while creating panorama. Error: ' + e.args[0])

    def create_panorama(self):
        """
        Checks if the start column is bigger than the end column and creates a new panorama image accordingly.
        :return: the new panorama image
        """
        self.update_slit_boundaries()
        if not self.check_boundaries():
            raise UserError(f'Please define valid starting and ending frames and columns!\n'
                            f'Frames range 0-{self.num_frames-1}, Columns range 0-{self.im_shape[1]}')
        try:
            if self.start_column <= self.end_column:
                return self.create_panorama_small_start()
            else:
                return self.create_panorama_big_start()
        except Exception as e:
            raise UserError(f'Could not create panorama image using the defined slice. Please select different end '
                            f'points.', e.args[0])

    def create_panorama_small_start(self):
        """
        Creates a new panorama image in the case where the starting column is smaller than the ending column
        :return: the new panorama image
        """
        if self.start_frame == self.end_frame:
            return self.frames[self.start_frame][:, self.start_column:self.end_column, :]
        col_range = self.end_column - self.start_column
        total_motion = int(np.sum(np.round(self.homographies[0, 2, self.start_frame:self.end_frame])))
        first_motion = int(round(self.homographies[0, 2, self.start_frame]))
        num_frames = self.end_frame - self.start_frame + 1
        start_pos = calculate_added_motion(self.start_column + first_motion, self.end_column, num_frames)
        panorama_width = total_motion + col_range
        panorama_im = np.zeros((self.im_shape[0], panorama_width, self.im_shape[2])).astype(np.uint8)
        panorama_col = 0

        if self.start_column == self.end_column:
            for i in range(num_frames - 1):
                motion = int(round(self.homographies[0, 2, self.start_frame + i]))
                if self.start_column + motion < self.im_shape[1]:
                    panorama_im[:, panorama_col: panorama_col + motion, :] = \
                        self.frames[self.start_frame + i][:, self.start_column: self.start_column + motion, :]
                else:
                    panorama_im[:, panorama_col: panorama_col + motion, :] = \
                        self.frames[self.start_frame + i][:, self.im_shape[1] - motion:, :]
                panorama_col += motion
            return panorama_im

        if self.end_column - self.start_column < first_motion and self.end_column != self.start_column:
            panorama_im[:, : self.end_column - self.start_column, :] = self.frames[self.start_frame][:, self.start_column: self.end_column, :]
            panorama_col += self.end_column - self.start_column
            self.end_column = self.start_column
            panorama_im[:, panorama_col:, :] = self.create_panorama_small_start()
            return panorama_im

        panorama_im[:, : start_pos[1] - start_pos[0] + first_motion, :] = \
            self.frames[self.start_frame][:, start_pos[0] - first_motion: start_pos[1], :]
        panorama_col += start_pos[1] - start_pos[0] + first_motion

        for i in range(1, num_frames):
            motion = int(round(self.homographies[0, 2, self.start_frame + i - 1]))
            panorama_im[:, panorama_col: panorama_col + start_pos[i + 1] - start_pos[i] + motion, :] = \
                self.frames[self.start_frame + i][:, start_pos[i] - motion: start_pos[i + 1], :]
            panorama_col += start_pos[i + 1] - start_pos[i] + motion
        return panorama_im

    def create_panorama_big_start(self):
        """
        Creates a new panorama image in the case where the starting column is bigger than the ending column
        :return: the new panorama image
        """
        if self.start_frame == self.end_frame:
            return self.frames[self.start_frame][:, self.end_column: self.start_column + 1, :]
        total_motion = int(np.sum(np.round(self.homographies[0, 2, self.start_frame:self.end_frame])))
        num_frames = self.end_frame - self.start_frame + 1
        num_cols = self.start_column - self.end_column + 1
        first_motion = int(round(self.homographies[0, 2, self.start_frame]))
        cur_start = self.start_column - first_motion
        panorama_width = total_motion
        if panorama_width <= 0:
            raise Exception('illegal panorama')
        panorama_im = np.zeros((self.im_shape[0], panorama_width, self.im_shape[2])).astype(np.uint8)
        panorama_col = 0
        for i in range(self.end_frame - self.start_frame - 1):
            added_motion = (num_cols - first_motion) // (num_frames - 2)
            next_motion = int(round(self.homographies[0, 2, self.start_frame + i + 1]))
            if i < ((num_cols - first_motion) % (num_frames - 2)):
                added_motion += 1
            cur_end = cur_start + next_motion - added_motion
            if cur_end < cur_start:
                cur_start, cur_end = cur_end, cur_start
            slit_width = cur_end - cur_start
            if cur_end > self.start_column:
                cur_end = self.start_column
                cur_start = cur_end - slit_width
            if cur_start < self.end_column:
                cur_start = self.end_column
                cur_end = cur_start + slit_width
            panorama_im[:, panorama_col: panorama_col + slit_width, :] = self.frames[self.start_frame + i][:, cur_start:cur_end, :]
            panorama_col += slit_width
            cur_start -= added_motion
        panorama_im = np.delete(panorama_im, np.where((panorama_im == 0).all(0)), axis=1)
        return panorama_im

    def check_boundaries(self):
        """
        Checks the validity of the starting and ending points for the slice defined by the user
        :return: True if the defined slice is valid, false otherwise.
        """
        if self.start_frame not in range(self.num_frames) or self.end_frame not in range(self.num_frames) or \
                self.start_frame > self.end_frame:
            return False
        if self.start_column not in range(self.im_shape[1] + 1) or self.end_column not in \
                range(self.im_shape[1] + 1):
            return False
        return True

    def update_slit_boundaries(self):
        """
        Updates the starting and ending frames and columns according to the values defined by the user
        """
        try:
            self.rotate_angle_label.destroy()
        except AttributeError:
            pass
        if self.start_column_entry.get():
            self.start_column = int(self.start_column_entry.get())
            self.start_column_entry.delete(0, 'end')
        if self.end_column_entry.get():
            self.end_column = int(self.end_column_entry.get())
            self.end_column_entry.delete(0, 'end')
        if self.start_frame_entry.get():
            self.start_frame = int(self.start_frame_entry.get())
            self.initial_start_frame = int(self.start_frame_entry.get())
            self.start_frame_entry.delete(0, 'end')
        if self.end_frame_entry.get():
            self.end_frame = int(self.end_frame_entry.get())
            self.initial_end_frame = int(self.end_frame_entry.get())
            self.end_frame_entry.delete(0, 'end')

        if self.move_frames_entry.get():
            self.start_frame += int(self.move_frames_entry.get())
            self.end_frame += int(self.move_frames_entry.get())
            self.move_frames_entry.delete(0, 'end')
        if self.move_columns_entry.get():
            self.start_column += int(self.move_columns_entry.get())
            self.end_column += int(self.move_columns_entry.get())
            self.move_columns_entry.delete(0, 'end')
        if self.rotate_slit_entry.get():
            self.rotate_angle = int(self.rotate_slit_entry.get())
            self.update_rotation_angle()
            self.rotate_slit_entry.delete(0, 'end')

    def update_rotation_angle(self):
        """
        Updates the boundaries of the slit according to the rotation angle defined by the user
        """
        self.rotate_angle_label = self.add_label(text=f'angle: {self.rotate_angle}', place=[390, 300])
        if 0 <= abs(self.rotate_angle) <= 45:
            change = (self.rotate_angle * self.im_shape[1]) // 90
            self.start_column = (self.im_shape[1] // 2) - change
            self.end_column = (self.im_shape[1] // 2) + change
            self.start_frame = self.initial_start_frame
            self.end_frame = self.initial_end_frame
        elif 45 < self.rotate_angle <= 90:
            self.start_column = 0
            self.end_column = self.im_shape[1] - 1
            num_frames = self.initial_end_frame - self.initial_start_frame
            change = (num_frames * (self.rotate_angle - 45)) // 90
            self.start_frame = self.initial_start_frame + change
            self.end_frame = self.initial_end_frame - change
        elif -90 <= self.rotate_angle < -45:
            num_frames = self.initial_end_frame - self.initial_start_frame
            change = (num_frames * (abs(self.rotate_angle) - 45)) // 90
            self.start_column = self.im_shape[1] - 1
            self.end_column = 0
            self.start_frame = self.initial_start_frame + change
            self.end_frame = self.initial_end_frame - change
        else:
            raise UserError("Please define a valid rotation angle between -90 and 90")

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
    WIDTH, HEIGHT = 500, 400
    BACKGROUND = 'grey'
    TITLE = 'X-Slit GUI'

    root = tk.Tk()
    root.title(TITLE)
    root.geometry('%sx%s' % (WIDTH, HEIGHT))

    app = GUI(root)  # , background=BACKGROUND)
    app.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.TRUE)
    app.mainloop()
