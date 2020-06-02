from tkinter import filedialog
from os import listdir
from GUI_helper import *


# working on the branch of x_slits

class GUI(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.directory = ''
        self.file_name = ''
        self.frames = []
        self.num_frames = 0
        self.homographies = None
        self.start_frame = None
        self.end_frame = None
        self.start_column = None
        self.end_column = None
        self.select_folder_button()
        self.motion_button()
        self.select_slice()
        self.move_slice()
        self.add_button(text='Show', place=[200, 320], command=self.create_slit)

    def select_folder_button(self):
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
        self.start_frame = self.add_entry(place=[90, 170], width=3)
        self.end_frame = self.add_entry(place=[147, 170], width=3)
        self.start_column = self.add_entry(place=[315, 170], width=3)
        self.end_column = self.add_entry(place=[372, 170], width=3)

    def move_slice(self):
        """
        Allows the user to move the selected slice, left-right, forward-backward and zoom in-zoom out.
        """
        self.add_label(text='Insert different values to create different space-time volume slices:', place=[15, 230])
        self.add_label(text='Left-Right (#pixels)', place=[15, 250])
        self.add_entry(place=[60, 270], width=4)
        self.add_label(text='Backward-Forward (#frames)', place=[150, 250])
        self.add_entry(place=[220, 270], width=4)
        self.add_label(text='Zoom in/out (degree)', place=[350, 250])
        self.add_entry(place=[400, 270], width=4)

    def load_dir(self):
        """
        Loads the dir the user selected and displays the number of frames in it and the size of an image
        """
        try:
            self.load_label.destroy()
        except AttributeError:
            pass
        # self.reset_fields()
        # todo: add try and accept for cases where there are other things in the folder than images
        self.directory = filedialog.askdirectory(initialdir="/", title="select dir") + '/'
        self.file_name = self.directory.split('/')[-2]
        print(self.directory)

        # load frames:
        self.frames = load_images(self.directory)
        if self.frames:
            self.num_frames = len(self.frames)
            self.load_label = self.add_label(text=f'Folder Name: {self.file_name}\n'
                                                  f'Number of Frames: {len(self.frames)}\n'
                                                  f'Frame size: {self.frames[0].shape[0]}x{self.frames[0].shape[1]}',
                                             place=[200, 10])
        else:
            print("error")
            # todo: display to the user an error message that the folder is empty

    def compute_motion(self):
        """
        Calculates the motion between every two consecutive frames in the sequence and saves it in a file
        '/Motion/<sequence_name>.csv'. If the file already exists, it loads this file instead of recomputing the motion.
        """

        try:
            if not self.directory:
                raise UserError('Please load a folder first!')

            self.homographies = np.genfromtxt('Motion/' + self.file_name + '.csv', delimiter=',') \
                .reshape((3, 3, self.num_frames - 1))

        except UserError as e:  # catch the error if the user didn't load a folder
            self.display_error(e.message)

        except IOError as e:  # if no motion file for the loaded folder was previously created, catch the IOError,
            # calcualte and save the motion
            self.homographies = np.zeros((3, 3, self.num_frames - 1))
            for i in range(self.num_frames - 1):
                self.homographies[:, :, i] = Homography(self.frames[i], self.frames[i + 1], translation_only=True)
            csv_data = self.homographies.reshape((9, self.num_frames - 1))
            np.savetxt('Motion/' + self.file_name + '.csv', csv_data, delimiter=',')

    def create_slit(self):
        """
        Calculates the panorama slit according to the values specified by the user and displays the image to the user.
        :return:
        """
        window = Toplevel(root)
        img = ImageTk.PhotoImage(Image.open('/Users/darkushin/Desktop/Studies/Computational-Photography/Ex2/Results/train-in-snow/panorama_frames0-245_cols100-327.jpg'))
        canvas = tk.Canvas(window, width=img.width(), height=img.height(),
                                borderwidth=0, highlightthickness=0)
        canvas.pack(expand=True)
        canvas.create_image(0, 0, image=img, anchor=tk.NW)
        canvas.img = img  # Keep reference.

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

    def display_error(self, err_msg):
        """
        Creates a new window with an error message for the user.
        :param err_msg: The message that should be displayed to the user
        """
        BACKGROUND = 'grey'
        TITLE = 'Error'
        err_window = Toplevel(root)
        err_window.title(TITLE)
        err_window.configure(background=BACKGROUND)
        err_label = tk.Label(err_window, text=err_msg)
        err_label.pack()
        err_button = tk.Button(err_window, text='Got it!', command=err_window.destroy)
        err_button.pack()


if __name__ == '__main__':
    WIDTH, HEIGHT = 500, 350
    BACKGROUND = 'grey'
    TITLE = 'X-Slit GUI'

    root = tk.Tk()
    root.title(TITLE)
    root.geometry('%sx%s' % (WIDTH, HEIGHT))
    # root.configure(background=BACKGROUND)

    app = GUI(root)  # , background=BACKGROUND)
    app.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.TRUE)
    app.mainloop()
