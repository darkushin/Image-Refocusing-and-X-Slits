from GUI_helper import *


# This file contains useful functions for using the program and visualizing the results, such as breaking a new input
# sequence into frames, creating a new video from the resulting frames and creating multiple panoramas.


def video2frames(file_name):
    """
    This function reads the given video and breaks it down into frames. Moreover, this function produces a 10x naive
    fast-forward video, by sampling every 10th frames uniformly
    :param file_name: The name of the video that should be produced.
    """
    # Create a VideoCapture object and read from input file
    cap = cv2.VideoCapture('../Videos/' + file_name + '.mp4')
    os.system('mkdir ../Data/' + file_name)

    # Check if camera opened successfully
    if (cap.isOpened() == False):
        print("Error opening video stream or file")

    # Read until video is completed
    i = 1
    while (cap.isOpened()):
        # Capture frame-by-frame
        ret, frame = cap.read()
        if ret:
            # Display the resulting frame
            cv2.imshow('Frame', frame)
            cv2.imwrite('../Data/' + file_name + '/' + file_name + str(i) + '.jpg', frame)

            # Press Q on keyboard to  exit
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break
        else:
            break
        i += 1

    cap.release()
    # Closes all the frames
    cv2.destroyAllWindows()


def frames2video(dir):
    """
    Creates a new output video from the frames in the specified dir.
    """
    frames = load_images(dir)
    im_shape = frames[-1].shape
    out = cv2.VideoWriter('../Results/train-in-snow-reversed.avi', cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 30,
                          (im_shape[1], im_shape[0]))

    for frame in frames:
        out.write(frame)

    out.release()


def reverse_video(dir):
    """
    Reverses the order of the frames in the sequence.
    """
    sequence = dir.split('/')[-1]
    images_path = sorted_alphanumeric(os.listdir(dir))
    i = len(images_path)
    for im_path in images_path:
        if im_path == '.DS_Store':
            continue
        im = BGR2RGB(cv2.imread(dir + '/' + im_path))
        plt.imsave(f'../Data/{sequence}/reversed-{i}.jpg', im)
        i -= 1


def create_panorama_small_start(start_frame, end_frame, start_column, end_column, frames, homographies):
    """
    Creates a new panorama image in the case where the starting column is smaller than the ending column
    :param start_frame: the first frame to use for the panorama
    :param end_frame: the last frame to use for the panorama
    :param start_column: the first column to use in the panorama
    :param end_column: the last column to use in the panorama
    :param frames: the loaded frames that should be used for creating the panorama
    :param homographies: the homographies between every consecutive frames in the sequence
    :return: the new panorama image
    """
    im_shape = frames[0].shape
    if start_frame == end_frame:
        return frames[start_frame][:, start_column:end_column, :]
    col_range = end_column - start_column
    total_motion = int(np.sum(np.round(homographies[0, 2, start_frame:end_frame])))
    first_motion = int(round(homographies[0, 2, start_frame]))
    num_frames = end_frame - start_frame + 1
    start_pos = calculate_added_motion(start_column + first_motion, end_column, num_frames)
    panorama_width = total_motion + col_range
    panorama_im = np.zeros((im_shape[0], panorama_width, im_shape[2])).astype(np.uint8)
    panorama_col = 0

    if start_column == end_column:
        for i in range(num_frames - 1):
            motion = int(round(homographies[0, 2, start_frame + i]))
            if start_column + motion < im_shape[1]:
                panorama_im[:, panorama_col: panorama_col + motion, :] = \
                    frames[start_frame + i][:, start_column: start_column + motion, :]
            else:
                panorama_im[:, panorama_col: panorama_col + motion, :] = \
                    frames[start_frame + i][:, im_shape[1] - motion:, :]
            panorama_col += motion
        return panorama_im

    if end_column - start_column < first_motion and end_column != start_column:
        panorama_im[:, : end_column - start_column, :] = frames[start_frame][:, start_column: end_column, :]
        panorama_col += end_column - start_column
        panorama_im[:, panorama_col:, :] = create_panorama_small_start(start_frame, end_frame, start_column,
                                                                       start_column, frames, homographies)
        return panorama_im

    panorama_im[:, : start_pos[1] - start_pos[0] + first_motion, :] = \
        frames[start_frame][:, start_pos[0] - first_motion: start_pos[1], :]
    panorama_col += start_pos[1] - start_pos[0] + first_motion

    for i in range(1, num_frames):
        # print(i)
        motion = int(round(homographies[0, 2, start_frame + i - 1]))
        if start_pos[i + 1] + motion <= im_shape[1]:
            panorama_im[:, panorama_col: panorama_col + start_pos[i + 1] - start_pos[i] + motion, :] = \
                frames[start_frame + i][:, start_pos[i]: start_pos[i + 1] + motion, :]
        else:
            panorama_im[:, panorama_col: panorama_col + start_pos[i + 1] - start_pos[i] + motion, :] = \
                frames[start_frame + i][:, start_pos[i] - motion: start_pos[i + 1], :]
        panorama_col += start_pos[i + 1] - start_pos[i] + motion
    return panorama_im


def create_panorama_big_start(start_frame, end_frame, start_column, end_column, frames, homographies):
    """
    Creates a new panorama image in the case where the starting column is bigger than the ending column
    :param start_frame: the first frame to use for the panorama
    :param end_frame: the last frame to use for the panorama
    :param start_column: the first column to use in the panorama
    :param end_column: the last column to use in the panorama
    :param frames: the loaded frames that should be used for creating the panorama
    :param homographies: the homographies between every consecutive frames in the sequence
    :return: the new panorama image
    """
    im_shape = frames[0].shape
    if start_frame == end_frame:
        return frames[start_frame][:, end_column: start_column + 1, :]
    total_motion = int(np.sum(np.round(homographies[0, 2, start_frame:end_frame])))
    num_frames = end_frame - start_frame + 1
    num_cols = start_column - end_column + 1
    first_motion = int(round(homographies[0, 2, start_frame]))
    cur_start = start_column - first_motion
    panorama_width = total_motion
    if panorama_width <= 0:
        raise Exception('illegal panorama')
    panorama_im = np.zeros((im_shape[0], panorama_width, im_shape[2])).astype(np.uint8)
    panorama_col = 0
    for i in range(end_frame - start_frame - 1):
        added_motion = (num_cols - first_motion) // (num_frames - 2)
        next_motion = int(round(homographies[0, 2, start_frame + i + 1]))
        if i < ((num_cols - first_motion) % (num_frames - 2)):
            added_motion += 1
        cur_end = cur_start + next_motion - added_motion
        if cur_end < cur_start:
            cur_start, cur_end = cur_end, cur_start
        slit_width = cur_end - cur_start
        if cur_end > start_column:
            cur_end = start_column
            cur_start = cur_end - slit_width
        if cur_start < end_column:
            cur_start = end_column
            cur_end = cur_start + slit_width
        panorama_im[:, panorama_col: panorama_col + slit_width, :] = frames[start_frame + i][:, cur_start:cur_end, :]
        panorama_col += slit_width
        cur_start -= added_motion
    panorama_im = np.delete(panorama_im, np.where((panorama_im == 0).all(0)), axis=1)
    return panorama_im


def create_panorama(start_frame, end_frame, start_column, end_column, frames, homographies):
    """
    Creates a new panorama image defined by the given end points
    :param start_frame: the first frame to use for the panorama
    :param end_frame: the last frame to use for the panorama
    :param start_column: the first column to use in the panorama
    :param end_column: the last column to use in the panorama
    :param frames: the loaded frames that should be used for creating the panorama
    :param homographies: the homographies between every consecutive frames in the sequence
    :return: the new panorama image
    """
    if start_column <= end_column:
        panorama_im = create_panorama_small_start(start_frame, end_frame, start_column, end_column, frames,
                                                  homographies)
    else:
        panorama_im = create_panorama_big_start(start_frame, end_frame, start_column, end_column, frames, homographies)
    return panorama_im


def produce_panorama_sequence(dir, start_frame, end_frame, start_column, end_column, fix_param=None):
    """
    Produces and saves a sequence of panoramas defined by the given parameters.
    :param dir: the directory of the frames that should be used for the panorama
    :param start_frame: the first frame to use for the panorama
    :param end_frame: the last frame to use for the panorama
    :param start_column: the first column to use in the panorama
    :param end_column: the last column to use in the panorama
    :param fix_param: defines which parameter should be fixed - columns or frames. If the given value is 'frames' then
    the produced panoramas will be all possible panoramas with the given frames and columns ranging from the given start
    column to the given end column. If the given value is 'cols' then the produced panoramas will be all possible
    panoramas with the fixed columns and frames ranging from the given start and end frames. If not specified the
    function will create a single panorama image from the defined end points.
    """
    sequence = dir.split('/')[-1]
    os.system(f'mkdir Results/{sequence}')

    # load the frames:
    frames = load_images(dir)
    file_name = dir.split('/')[-1]
    num_frames = len(frames)

    # compute all homographies:
    try:
        homographies = np.genfromtxt('../Motion/' + file_name + '.csv', delimiter=',').reshape((3, 3, num_frames - 1))
    except IOError:
        homographies = compute_homographies(frames, translation_only=True)
        csv_data = homographies.reshape((9, num_frames - 1))
        np.savetxt('../Motion/' + sequence + '.csv', csv_data, delimiter=',')

    frames = validate_motion_direction(frames)

    if fix_param == 'frames':
        min_col = min(start_column, end_column)
        max_col = max(start_column, end_column)
        for j in range(min_col, max_col // 2):
            panorama_im = create_panorama(start_frame, end_frame, j, end_column - j, frames, homographies)
            plt.imsave(f'../Results/{sequence}/panorama_frames{start_frame}-{end_frame}_cols{j}-{end_column - j}.jpg',
                       BGR2RGB(panorama_im))

    elif fix_param == 'cols':
        num_frames = end_frame - start_frame + 1
        for j in range(num_frames // 2):
            panorama_im = create_panorama(start_frame + j, end_frame - j, start_column, end_column, frames, homographies)
            plt.imsave(f'../Results/{sequence}/panorama_frames{start_frame+j}-{end_frame-j}_cols{start_column}-{end_column}.jpg',
                       BGR2RGB(panorama_im))

    else:
        panorama_im = create_panorama(start_frame, end_frame, start_column, end_column, frames, homographies)
        plt.imsave(f'../Results/{sequence}/panorama_frames{start_frame}-{end_frame}_cols{start_column}-{end_column}.jpg',
                   BGR2RGB(panorama_im))


def validate_motion_direction(frames):
    """
    Validates that the given sequence is taken from left to right. If the sequence was taken from right to left,
    this function reverses the frames.
    """
    test_num = max(int(len(frames) // 10), 1)
    test_homographies = np.zeros((3, 3, test_num))
    for i in range(test_num):
        test_homographies[:, :, i] = Homography(frames[i], frames[i + 1], translation_only=True)
    if np.sum(test_homographies[0, 2, :]) < 0:
        frames = frames[::-1]
    return frames


def create_left_right_panoramas(dir):
    """
    Creates all possible panoramas with the same starting and ending columns. This creates a left to right view.
    """
    sequence = dir.split('/')[-1]
    os.system(f'mkdir ../Results/{sequence}')

    # load the frames:
    frames = load_images(dir)
    file_name = dir.split('/')[-1]
    num_frames = len(frames)

    # compute all homographies:
    try:
        homographies = np.genfromtxt('../Motion/' + file_name + '.csv', delimiter=',').reshape((3, 3, num_frames - 1))
    except IOError:
        homographies = compute_homographies(frames, translation_only=True)
        csv_data = homographies.reshape((9, num_frames - 1))
        np.savetxt('../Motion/' + sequence + '.csv', csv_data, delimiter=',')

    frames = validate_motion_direction(frames)
    im_shape = frames[0].shape
    for i in range(im_shape[1]):
        panorama_im = create_panorama(0, num_frames-1, i, i, frames, homographies)
        plt.imsave(f'../Results/{sequence}/panorama_frames{0}-{num_frames-1}_cols{i}-{i}.jpg',
                   BGR2RGB(panorama_im))


# create_left_right_panoramas('../Data/Nutella')
produce_panorama_sequence('../Data/Nutella', 0, 307, 639, 0)
# frames2video('../Data/train-in-snow-reversed')
# reverse_video('../Data/train-in-snow')
# video2frames('Nutella')
