# Light Fields
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
 	 - 'Left-Right' and 'Up-Down' buttons and entries. Pressing once every '+' and '-' button will shift the frames lnearly by +0.5 and -0.5 pixels respectively. Entering a value to the entries under these buttons will shift the images linearly by the entered value. After defining the desired changes, press the 'Show' button in the bottom to display the new refocused image, calculated according to the specified motion. After the image is displayed, a new label will appear in the GUI, indicating the motion that was used to calculate the output image.
	 - Pressing the 'Select Area' button. Pressing this button will open a new window with the middle image of the sequence as reference. Select a desired object to focus on in the image using the mouse and press the 'Done' button. Pressing this button will close the reference frame and create a new output image where the focus is on the selected area.
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

# Results

## Lego Sequence:

### Reference Frame
![Lego138](https://user-images.githubusercontent.com/61732335/84602047-57824b80-ae8d-11ea-9ba8-161e725c88e1.jpg)


### Focus on Airplane & Trucks
![lego-close](https://user-images.githubusercontent.com/61732335/84602128-c65fa480-ae8d-11ea-9019-4d4a4841068a.png)


### Focus on Chairs
![lego-mid](https://user-images.githubusercontent.com/61732335/84602133-d37c9380-ae8d-11ea-9159-b6bad85fee23.png)			

### Focus on Helicopter & Background
![lego-far](https://user-images.githubusercontent.com/61732335/84602099-adef8a00-ae8d-11ea-82ec-06d43d1510df.png)



## Banana Sequence:

### Reference Frame
![rsz_capture_00011](https://user-images.githubusercontent.com/61732335/84602288-e5126b00-ae8e-11ea-9f9d-ea3368b9db65.jpg)


### Focus on Ball
![banana-close](https://user-images.githubusercontent.com/61732335/84602228-8220d400-ae8e-11ea-955c-a221e222b3d4.png)


### Focus on Apple
![banana-mid](https://user-images.githubusercontent.com/61732335/84602232-85b45b00-ae8e-11ea-97e7-c98c12e03c1f.png)			

### Focus on Book
![banana-far](https://user-images.githubusercontent.com/61732335/84602229-83520100-ae8e-11ea-8dc4-9498a7784dac.png)


## Treasure Sequence:

### Reference Frame
![i](https://user-images.githubusercontent.com/61732335/84602800-9070ef00-ae92-11ea-9941-05ae3111f586.png)


### Focus on Close Objects
![treasure-close](https://user-images.githubusercontent.com/61732335/84602746-3ec86480-ae92-11ea-833c-df7bc92f1029.png)


### Focus on Middle Objects
![treasure-mid](https://user-images.githubusercontent.com/61732335/84602762-54d62500-ae92-11ea-9542-0c69d842ad42.png)			

### Focus on Far Objects
![treasure-far](https://user-images.githubusercontent.com/61732335/84602754-4b4cbd00-ae92-11ea-87d6-584f7e6e9351.png)



# Part II – X-Slits
In this part I will explain in detail the implementation and results for the x-slits task.

This GUI allows the user to select an image sequence and create panorama images from different viewpoints, representing different slices in the Space-Time volume. The input to the GUI is a video sequence, broken down into frames.

## Motion Computation:
The motion direction in the sequence can be left-to-right as well as right-to-left. In the case of right-to-left motion, I refer to the motion in absolute values as the translation is negative. The motion between the frames is computed for every two consecutive frames as explained in Part I, hence in this part as well I don’t assume the motion in the sequence is constant.
In contrast to Part I, for the X-Slits task I assume the motion in the sequence is a pure-translation motion, hence the ‘Translation-Only’ option from the Refocusing-GUI isn’t presented to the user and is used by default.

## Creating Panoramas:
Next, we will discuss three different options for creating a panorama image:

**Equal Starting & Ending Columns:** This case represents a vertical slit in the Space-Time volume. Assume start_col = end_col = k. From every image in the sequence, the starting column of the part we take from the image should be the k’th column in the image. In order to create a panorama without holes or overlaps the width of the part we take has to change dynamically according to the motion between every two frames. For example, if the motion between frame i and frame i+1 is t in the x direction and the starting column is k, then from frame i we will use the columns ranging from k to k+t. This results in a panorama image of width equal to the sum of all the translations between consecutive frames in the sequence.

**Smaller Starting Than Ending Columns:** This case represents a slice in the Space-Time volume with a positive angle (1-90). Assume the starting column is k and the ending column is l (>k). In this case, the starting column of the part we take from every image in the sequence has to become bigger as we progress to more advanced frames in the sequence, otherwise we will get an equal panorama image to the one explained before. Hence, the width of the part we take from every image has to be wider than the actual motion between this frame and its consecutive frame. For example, assume the motion between frame i and frame i+1 is t and the defined starting and ending columns are k and l respectively (k< l). Denote by N the number of frames that should be used for creating the panorama. Under those notations, the parts taken from the i'th image are the columns in range k to k+t+(l-k)/N. Notice that in this method an object that was in column k+t+(l-k)/N in frame i, will be in column k+(l-k)/N in frame i+1. Therefore, in order to avoid overlaps and holes in the panorama image the first column that should be used from frame i+1 is k+(l-k)/N≥k. Hence, we receive a panorama image with increasing starting columns for every frame as desired.
Since we take from every frame a part wider than the actual motion between this and its consecutive frame, the width of the resulting panorama image is equal to the sum of the motion between all frames in the sequence plus the difference between the ending and starting columns (l-k).

**Larger Starting Than Ending Columns:** This case represents a slice in the Space-Time volume with a negative angle (-1-(-90)). Assume the starting column is k and the ending column is l (<k). Analogically to the previous case, in this case, the starting column of the part we take from every image in the sequence has to become smaller as we progress to more advanced frames in the sequence. Hence, the width of the part we take from every image has to be smaller than the actual motion between this frame and its consecutive frame. For example, assume the motion between frame i and frame i+1 is t and the defined starting and ending columns are k and l respectively (k> l). Denote by N the number of frames that should be used for creating the panorama. Under those notations, the parts taken from the i'th image are the columns in range k to k-t+(l-k)/N. Notice that in this method an object that was in column k+t– (l-k)/N  in frame i, will be in column k– (l-k)/N in frame i+1. Therefore, in order to avoid overlaps and holes in the panorama image the first column that should be used from frame i+1 is k– (l-k)/N≤k. Hence, we receive a panorama image with decreasing starting columns for every frame as desired.
Since we take from every frame a part smaller than the actual motion between this and its consecutive frame, the width of the resulting panorama image is equal to the sum of the motions between all frames in the sequence minus the difference between the starting and ending columns (k-l). Notice, using this method there are panoramas that might appear weird with duplications of objects. Moreover, not all starting and ending columns will result a valid panorama image as it might happen that the motion between the frames is smaller than the difference between the starting and ending columns.

## Processing Speed: 
-	Motion Computation – as before, the speed of the motion computation depends on the number of frames in the sequence. As the sequences for the x-slits task may contain a few hundred images, the motion computation might take slightly longer then in the case of refocusing. For all sequences I used, this part didn’t take more than a few seconds (less than 4)
-	Creating Panoramas – Once the motion between all frames in the sequence is computed, creating every individual panorama image is usually a matter of a few milliseconds. This part might take up to 1 second from the moment when pressing the ‘Show’ button until the resulting panorama image is displayed to the user.

## Usage Instructions:
1.	Run the X-Slits-Task.py program.
2.	Press the ‘Select Folder' button. In the new opened window, navigate to the folder containing the desired sequence.
3.	Press the 'Compute Motion' button in order to compute the motion between every two consecutive frames in the sequence.
4.	Define the initial slice in the Space-Time volume by filling the four available entries representing the start frame, end frame, start column and end column, by this order. Each number should be entered in the relevant entry. The possible values are from 0 to NUM_FRAMES-1 for the frame entries, and 0 to IMAGE_WIDTH-1 for the column entries. For your convenience, after selecting a sequence, the number of frames and the dimensions of an image in the sequence are presented in the upper-right corner of the GUI. The image shape is in the format of HEIGHT x WIDTH.
5.	After defining the endpoints, a panorama image can be created by pressing the ‘Show’ button in the bottom of the GUI. Pressing this window will open a new image with the resulting panorama image that was computed according to the endpoints defined by the user. For your convenience, after pressing this button a new label will appear above it, indicating the frames and columns ranges that were used to create the displayed panorama. The endpoints entries are being cleared to avoid confusion.
6. 	Create new panoramas: after defining the initial endpoints of the panorama, new panoramas from different viewing points can be created in one of the following ways:
	- **Directly changing** the slice endpoints by inserting values as explain in step 4.
	- **Backward-Forward entry:** this entry allows the user to insert a number to move the frames that are being moved forward/backward. For example, if the previous panorama was created using frames i and j as the start and end frames respectively, then filling the number n in this entry will create a panorama image using frames i+n to j+n and the same columns as defined before. In case i+n < 0 or j+n > NUM_FRAMES-1 an error message is displayed to the user (see Notes).
	- **Left-Right entry:** this entry allows the user to shift the start and end columns to the left/right. For example, if the previous panorama was created using columns k and l as the start and end columns respectively, then inserting the number n in this entry will create a panorama using the same frames as before but columns ranging from k+n to l+n. As in the previous case, if k+n < 0 or l+n>IM_WIDTH-1 an error message is displayed to the user (see Notes).
	- **Zoom-in/out entry:** this entry allows the user to insert an angle (-90 to 90) in which the current slice of the Space-Time volume should be rotated. * Inserting the value 0 will create a panorama defined by a vertical slice in the space time volume through the center of every frame. For values between 1 to 45 the used frames are fixed and the columns range changes. Notice that the frames that are used in this case are the frames defined by the user (not necessarily all the frames in the sequence). 
For values between 46 to 90 the used columns are fixed to be 0 and IM_WIDTH-1 and the frames that are being used are changing. This created a zoom-in affect as when the angle becomes larger the resulting panorama is smaller. Negative values have the exact analogical affect (same computation but defining the start column as bigger than the end column).
For your convenience, after inserting a value to this entry, the entered value is displayed below the entry after creating the panorama image.

**Notes:**
1.	For using a different sequence go back to step 1.
2.	As in the refocusing case, the motion between every two consecutive frames is calculated only for the first time the sequence is used. If the sequence is re-used, then the motion is loaded from a .csv file saving this information. If recomputing the motion is desired, then the motion file of the sequence should be deleted first. The motion file of the sequence has the same name as the sequence folder and should be located in the Motion folder.
3.	If the user defined an invalid slice of the Space-Time volume, i.e. start frame < 0, end frame > NUM_FRAMES-1, start/end column < 0 or > IM_WIDTH-1, an error is displayed to the user. In the error message the user can see the actual ranges for the frames and columns that can be defined.

## I/O Formats:
As explained before, the user is first expected to define the initial endpoints for the slice using the four entries representing the start frame, end frame, start column and end column.
Next, the user can change the slice of the Space-Time volume using the entries as explained in point 6 in the User Instructions section.

## Captured Sequence:
For this part I captured the Nutella sequence. This sequence was taken from left to right and in the pictured scene there are multiple objects in different depths in the real world. Even though this sequences was taken indoors, there is a large translation between the first and last frames in the sequence, which make it suitable for this task and results interesting panoramas.
Next, the results of this sequence, along with the results of more sequences are shown. These results are attached to the submission in a Result folder as well. The original Nutella sequence can be found under the Data folder.


# Results

## Apple Sequence:

### First Image First Column – Last Image First Column
![apples-0-0](https://user-images.githubusercontent.com/61732335/84602527-ada4be00-ae90-11ea-9931-2390cfbfbe1c.png)

### First Image Last Column – Last Image Last Column
![apples-383-383](https://user-images.githubusercontent.com/61732335/84602544-d036d700-ae90-11ea-8716-00523036d000.png)

### First Image First Column – Last Image Last Column
![apples-0-383](https://user-images.githubusercontent.com/61732335/84602536-bc8b7080-ae90-11ea-9f8d-c1d14702a998.png)

### First Image Last Column – Last Image First Column
![apples-383-0](https://user-images.githubusercontent.com/61732335/84602541-c90fc900-ae90-11ea-8b9d-a0b3debcf9a2.png)


## Nutella Sequence:

### First Image First Column – Last Image First Column
![apples-0-0](https://user-images.githubusercontent.com/61732335/84602601-5bb06800-ae91-11ea-8f80-5d391c90a6b6.png)

### First Image Last Column – Last Image Last Column
![apples-639-639](https://user-images.githubusercontent.com/61732335/84602618-7a166380-ae91-11ea-9413-9e27a8ca9ea5.png)

### First Image First Column – Last Image Last Column
![apples-0-639](https://user-images.githubusercontent.com/61732335/84602608-679c2a00-ae91-11ea-81a3-bc7d50ef2a9b.png)

### First Image Last Column – Last Image First Column
![apples-639-0](https://user-images.githubusercontent.com/61732335/84602617-7682dc80-ae91-11ea-822b-7871c298b7b0.png)


## EmekRefaim Sequence:

### First Image First Column – Last Image First Column
![EmekRefaim-0-0](https://user-images.githubusercontent.com/61732335/84602677-e002eb00-ae91-11ea-8253-b3dcf5cd2cf9.png)

### First Image Last Column – Last Image Last Column
![EmekRefaim-239-239](https://user-images.githubusercontent.com/61732335/84602700-f01aca80-ae91-11ea-9f59-7ede5df34733.png)

### First Image First Column – Last Image Last Column
![EmekRefaim-0-239](https://user-images.githubusercontent.com/61732335/84602685-e7c28f80-ae91-11ea-8cc9-0cfa314fdeb9.png)

### First Image Last Column – Last Image First Column
![EmekRefaim-239-0](https://user-images.githubusercontent.com/61732335/84602692-ed1fda00-ae91-11ea-8b45-9a1d61095727.png)


