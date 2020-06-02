from tkinter import filedialog
from os import listdir
from GUI_helper import *

# working on the branch of x_slits

class GUI(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.directory = ''
        self.frames = []
        self.num_frames = 0
        self.select_folder_button()
        self.motion_button()
        self.select_slice()
        self.move_slice()
        self.add_button(text='Show', place=[200, 320])

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
        self.add_label(text='Expected input: 4 numbers separated with a comma', place=[15, 150])
        self.add_label(text='indicating the start frame, start col, end frame, end col', place=[15, 170])
        self.add_entry(place=[15, 190])

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
        # self.file_name = self.directory.split('/')[-2]
        print(self.directory)

        # load frames:
        self.frames = load_images(self.directory)
        if self.frames:
            self.num_frames = len(self.frames)
            self.load_label = self.add_label(text=f'Folder Name: {self.directory.split("/")[-2]}\n'
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
            self.homographies = np.genfromtxt('Motion/' + self.file_name + '.csv', delimiter=',') \
                .reshape((3, 3, self.num_frames - 1))
        except Exception as e:
            self.homographies = np.zeros((3, 3, self.num_frames - 1))
            for i in range(self.num_frames - 1):
                self.homographies[:, :, i] = Homography(self.frames[i], self.frames[i + 1],
                                                        translation_only=self.trans_only_var.get())
            csv_data = self.homographies.reshape((9, self.num_frames - 1))
            np.savetxt('Motion/' + self.file_name + '.csv', csv_data, delimiter=',')

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
    TITLE = 'X-Slit GUI'

    root = tk.Tk()
    root.title(TITLE)
    root.geometry('%sx%s' % (WIDTH, HEIGHT))
    # root.configure(background=BACKGROUND)

    app = GUI(root)  # , background=BACKGROUND)
    app.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.TRUE)
    app.mainloop()
