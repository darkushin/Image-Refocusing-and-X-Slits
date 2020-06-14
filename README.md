# Image-Refocusing-and-X-Slits
This file includes detailed information about digital refocusing and creating X-Slits

# Part I – Image Refocusing
In this part I will explain in detail the implementation and results for the refocusing task.
This GUI allows the user to select an image sequence and change the focus on different objects in the pictured scene. The input to the GUI is a video sequence, broken down into frames.

## Motion Computation:
The motion direction in the sequence can be left-to-right as well as right-to-left. The motion between the frames is computed for every two consecutive frames, hence I don’t assume the motion in the sequence is constant. However, I assume the motion in the sequence is in a constant direction, i.e. if the sequence is taken from left to write then I assume the motion between every two consecutive frames is ≥0 and in particular not negative. For example, in the case of the ‘apples’ sequence the last frame should be omitted, as the translation between the one before last and the last frames is -1, although the sequence direction is from left to right.
The motion computation itself was done by first detecting feature points in every two consecutive frames and then computing the transformation that best fits the feature points using Ransac. The resulting transformation is a 3×3 matrix, defined by 3 parameters:
θ – rotation angle, dx – translation in the x direction and dy – translation in the y direction between the two frames. Hence, the resulting transformation is of the form:

![Untitled](https://user-images.githubusercontent.com/61732335/84597485-e6cb3700-ae6c-11ea-904e-6cc5becb2de6.png)

**Translation-only sequences**: Even though I don’t assume the input sequence to be a pure-translation sequence, for such sequences I allow the user to indicate that this is a pure-translation sequence by checking the ‘Translation-Only’ checkbox next to the ‘Compute Motion’ button. In this case, the transformations between every two consecutive frames will be consisted of a 3×3 matrix where the upper 2×2 part of the matrix is the identity matrix and the last column of the matrix represents the translation in the x and y directions. Hence, the resulting transformation in this case is of the form:

![Untitled 2](https://user-images.githubusercontent.com/61732335/84597541-3d387580-ae6d-11ea-8009-df7a8b5e236c.png)

## Image corrections:  
After computing the motion between every two consecutive frames, I aligned all images with respect to a common reference frame. This was done only once for every loaded sequence. The middle frame of the sequence was taken as the reference frame and the alignment was done as follows:
Denote by T_i,T_(i+1),T_(i+2) the transformation between the consecutive frames i and i+1, i+1 and i+2, i+2 and i+3 respectively. Under this notation, assume we wish to find the transformation between frame i and frame i+3. Instead of calculating it directly by looking for feature points in both images and finding the transformation that best fits the feature points as described before, we may use the composition of T_i,T_(i+1),T_(i+2). Hence, the transformation from frame i to frame i+2 can be computed as T_(i,i+2)=T_(i+2)∘T_(i+1)∘T_i .
With this observation at hand, the image alignment is performed by first computing the transformation of every frame i in the sequence to the common reference frame m. Then all images are warped to the same coordinates system using the computed transformations.

## Changing the Focus:
This GUI allows the user to change the focus of the resulting image in two ways:
1.	Using the ‘+’ and ‘-‘ buttons which allow the user to translate the image +0.5 and -0.5 pixels respectively in the chosen axis. Pressing the ‘+’ button under the ‘Left-Right’ label will translate all images half a pixel two the right, whereas pressing the ‘+’ button under the ‘Up-Down’ button will translate all images up.
Besides using the ‘+’ and ‘-‘ button, the user can also enter the desired translation directly by inserting a number to the matching entries below these buttons. Inserting a number (-x) to the entry below the ‘Left-Right’ label, will translate all images x pixels to the left.
2.	Using the ‘Select Area’ button. Pressing on this button will open a new window with the reference frame of the sequence (the middle image in the sequence). In this window, the user can use the mouse to select the are that should become focused (see the Notes section under Usage Instructions below for details how to select the area). Selecting a focus area in this matter, will result a new output image where the focus is on the area selected by the user.

**Image Shifting:** Shifting the images was performed linearly. After aligning the images in the sequence with respect to the reference frame, shifting the images was done in the following way: denote by dx (assume dx > 0) the desired translation as defined by the user, then every frame i in the sequence was shifted by dx⋅i pixels to the right, i.e. frame 0 wasn’t shifted and frame N was shifted by dx⋅N pixels to the right. Assume we wish to shift an image in x pixels to the right, the shifting itself was done by filling the first x columns of the output image with zeros and the rest of the image with the values of the aligned image from the first column until the last column-x. A similar logic was used for shifting left, up and down.
**Notes:**
	If the desired translation dx is not a round number, then the output image is computed as the mean of two images – one with translation of floor(dx) and one with translation of ceil(dx).
	Shifting an image is always done using the aligned image and not a previously shifted image. This is done in order to avoid information lose, for example in the case of left shifting followed by right shifting.

**Area Selection:** Refocusing the image using the area selection is done by the following logic:
For every two consecutive frames, instead of looking for feature points in the entire image, the feature points are selected only from the area selected by the user. This way, the computed translations are very accurate for the area the user defined, and less accurate for transforming other regions of the image. Hence, when computing the median of the translated images, the area selected by the user should be under focus, whereas the other regions in the image should be blurred. This method has a small limitation – when using a too small area or an area with small gradients, it might happen that not enough feature points will be detected. In this case, an error message will be displayed to the user, asking to select a larger or different area in the image.

## Processing Speed: 
-	**Motion Computation** – the speed of the motion computation depends on the number of frames in the sequence. As the sequences for the refocusing task usually consist of a few dozen images only, this computation is performed very fast, usually in less the 1 second.
-	**Refocusing** – Again, as these sequences don’t consist of a lot of images this part might take up to 1 second from the moment when pressing the ‘Show’ button until the new refocused image is displayed to the user.

## Usage Instructions:
1.	Run the Refocusing-Task.py program.
2.	Press the 'Select Folder' button. In the new opened window, navigate to the folder containing the desired sequence.
3.	Press the 'Compute Motion' button in order to compute the motion between every two consecutive frames in the sequence. If the sequence is a pure translation sequence, it is recommended to check the 'Translation-Only' checkbox BEFORE pressing the 'Compute Motion' button for better results.
4.	Focus on different objects in the pictured scene. This can be done in two ways:
  a. 'Left-Right' and 'Up-Down' buttons and entries. Pressing once every '+' and '-' button will shift the frames linearly by +0.5 and -0.5 pixels respectively. Entering a value to the entries under these buttons will shift the images linearly by the entered value. After defining the desired changes, press the 'Show' button in the bottom to display the new refocused image, calculated according to the specified motion. After the image is displayed, a new label will appear in the GUI, indicating the motion that was used to calculate the output image.
  b. Pressing the 'Select Area' button. Pressing this button will open a new window with the middle image of the sequence as reference. Select a desired object to focus on in the image using the mouse and press the 'Done' button. Pressing this button will close the reference frame and create a new output image where the focus is on the selected area.
5.	Using Mean or Median: before pressing the ‘Show’ button the user is given the option to choose whether to compute the refocused image using the median or the mean of all the aligned and translated images. The default option is using the mean, but for the treasure sequence (see Results section) I found the median to produce better results.

**Notes:**
1.	For using a different sequence go back to step 1.
2.	The motion between every two consecutive frames is calculated only for the first time the sequence is used. If the sequence is re-used, then the motion is loaded from a .csv file saving this information. If recomputing the motion is desired, then the motion file of the sequence should be deleted first. The motion file of the sequence has the same name as the sequence folder and should be located in the Motion folder.
3.	Direct area selection – as explained before, pressing the 'Select Area' button will open a new window with the reference frame. In this window, do a left click with the mouse in the upper-left corner of the area you wish to focus on and drag the mouse (while holding it clicked) to the lower-right corner of the desired area. This will draw a doted rectangle on the image, indicating the area selected by the user. Changing the selected area can be done by the same logic again. After the user is satisfied with the selected region, the ‘Done’ button should be pressed. Pressing this button will close the current window and open a new window displaying the refocused image, where the focus is on the area selected by the user.

## I/O Formats:
As explained before the user can change the focus manually using the ‘+’ and ‘-‘ buttons, where each button translates the image in ±0.5 pixels, or by changing the motion directly by filling the desired motion in the entries bellow those buttons.

## Captured Sequence:
For this part I captured the Lego sequence. This sequence was taken from left to right and in the pictured scene there are multiple objects in different depths in the real world.
Next, the results of this sequence, along with the results of more sequences are shown. These results are attached to the submission in a Result folder as well. The original Lego sequence can be found under the Data folder.

