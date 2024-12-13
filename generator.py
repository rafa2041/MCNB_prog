import os, json, pickle
import numpy as np
import pandas as pd
import string
import random
from OpenGL.GL import *
import random
import pygame


class Exp():

    def __init__(self, subj_ID, n_list, num_rounds, proportion_repeats, 
    im_h=300, im_w=300, stim_interval=2, stim_duration=0.5):

        upper_list = ['P', 'Q', 'A', 'M', 'Z', 'X', 'K', 'N', 'T']
        self.num_elements = len(upper_list)

        shape_list = [0, 1, 2]
        color_list = [[255,0,0],[0,255,0], [0,0,255]]
        
        # basic params
        self.subj_ID = subj_ID
        self.num_rounds = num_rounds
        self.proportion_repeats = proportion_repeats
        self.n_list = n_list

        #Stimuli params
        self.shapes_and_colors = []
        self.letters_list = upper_list

        self.shapes_colors_list = []
        for i in shape_list:
            for j in color_list:
                self.shapes_colors_list.append([i,j])
        

        #Stimuli lists
        self.stim_indeces = []
        self.stim_locs = []
        
        # image params
        self.im_h = im_h
        self.im_w = im_w

        # timing params
        self.stim_interval = stim_interval
        self.stim_duration = stim_duration

        # data collection
        self.fullData = {}
        self.fullData['ID'] = self.subj_ID
        self.fullData['true_vals_letters'] = np.zeros((len(n_list), num_rounds))
        self.fullData['responses_letters'] = np.zeros((len(n_list), num_rounds))
        self.fullData['true_vals_shapes'] = np.zeros((len(n_list), num_rounds))
        self.fullData['responses_shapes'] = np.zeros((len(n_list), num_rounds))

    #From Aoran: create the list of stimuli
    def makeNback(self, k, n_trials, n_back_level, target_proportion):
        stim_sequence = random.choices(range(k), k=n_trials)  # 30 random numbers between 0-17
        n_targets = int(target_proportion * n_trials)  # number of target trials 
        
        # first count natural matches
        natural_targets = []
        for i in range(n_back_level, n_trials):
            if stim_sequence[i] % 9 == stim_sequence[i - n_back_level] % 9:  # check only the "letter" part, ignoring case
                natural_targets.append(i)
        
        # truncate natural matches if >20% of total trials
        if len(natural_targets) > n_targets:
            excess_targets = len(natural_targets) - n_targets
            extra_targets = random.sample(natural_targets, excess_targets)  # randomly remove extras
            for target_index in extra_targets:
                stim_sequence[target_index] = random.choice([x for x in range(18) if x % 9 != stim_sequence[target_index - n_back_level] % 9])  # replace with non-matching number
        
        # recheck natural matches 
        natural_targets = [i for i in range(n_back_level, n_trials) if stim_sequence[i] % 9 == stim_sequence[i - n_back_level] % 9]
        
        # add missing targets if natural matches are not enough
        total_targets = len(natural_targets)  # number of targets present
        if total_targets < n_targets:
            missing_targets = n_targets - total_targets  # calculate # of targets are missing
            available_positions = [i for i in range(n_back_level, n_trials) if i not in natural_targets]
            force_positions = random.sample(available_positions, missing_targets)  # force targets in these positions
            
            for target_index in force_positions:
                # ensuring N-back logic 
                stim_sequence[target_index] = stim_sequence[target_index - n_back_level]  
                natural_targets.append(target_index)  # add to the list of targets
        
        # final check 
        actual_targets = [i for i in range(n_back_level, n_trials) if stim_sequence[i] % 9 == stim_sequence[i - n_back_level] % 9]

        # if there are still too many, remove extra targets
        if len(actual_targets) > n_targets:
            excess_targets = len(actual_targets) - n_targets
            extra_targets = random.sample(actual_targets, excess_targets)
            for target_index in extra_targets:
                stim_sequence[target_index] = random.choice([x for x in range(18) if x % 9 != stim_sequence[target_index - n_back_level] % 9])

        # recheck to ensure exactly 6 targets exist
        #In case we couldn't remove it, take it into account
        repeatLocs = np.zeros((n_trials))
        repeatLocsEnd = np.zeros((n_trials))
        for i in range(n_trials-n_back_level):
            repeatLocs[i] = stim_sequence[i+n_back_level] == stim_sequence[i]
        repeatLocsEnd[n_back_level:n_trials] = repeatLocs[0:n_trials-n_back_level]

        return stim_sequence, repeatLocsEnd

    def makeNback2(self, input_length, size, n, p):
        '''
        INPUT PARAMETERS
        elements: any python list
        size: length of the output list
        n: value of the n-back task
        p: proportion of stimuli which will be repeated in n-back fashion

        OUTPUTS
        result: list of length size containing
                stimuli selected from elements and arranged according to n-back task
        repeatLocs: list of length size. Equals 1 at locations where a repetition will occur
        '''
        elements = range(input_length)
        numRepeats = round(p*size)

        result = []
        # Ensure that there are no unintended repetitions
        for i in range(size):
            available_elems = [elem for elem in elements if i < n or result[i - n] != elements]
            if not available_elems:
                raise ValueError("Not enough elements to satisfy the non-repeating condition.")
            result.append(random.choice(available_elems))

        result = np.zeros(size) - 1

        #Randomly generate the locations which will have repeated elements
        repeatLocs = np.zeros((size))
        repeatLocsEnd = np.zeros((size))
        repeatLocs[random.sample(range(size-n), numRepeats)] = 1
        repeatLocsEnd[n:size] = repeatLocs[0:size-n]

        result = np.array(result)

        for i in range(size-n):
            if repeatLocs[i] or repeatLocsEnd[i]: 
                num = random.choice(elements)
                result[i] = num

        for i in range(size-n):
            if repeatLocs[i]: 
                result[i+n] = result[i]

        for i in range(size):
            if result[i] == -1:
                allowed_numbers = [x for x in elements if (x != result[(i-n)%size] and x!= result[(i+n)%size])]
                result[i] = random.choice(allowed_numbers)

        result = [int(x) for x in result]
        repeatLocsEnd = [int(x) for x in repeatLocsEnd]
        return result, repeatLocsEnd

    def generate_trials(self, n):
        self.stim_indeces, self.stim_locs = self.makeNback2(self.num_elements, self.num_rounds, n, self.proportion_repeats)

    def save_expt(self):
        # this is how to save a pandas dict to csv

        newpath = f'./exported_data/ID_{self.subj_ID}'
        if not os.path.exists(newpath):
            os.makedirs(newpath)
 
        true_vals_letters_frame = pd.DataFrame(self.fullData['true_vals_letters'])
        responses_letters_frame = pd.DataFrame(self.fullData['responses_letters'])
        true_vals_shapes_frame = pd.DataFrame(self.fullData['true_vals_shapes'])
        responses_shapes_frame = pd.DataFrame(self.fullData['responses_shapes'])

        true_vals_letters_frame.to_csv(f'./exported_data/ID_{self.subj_ID}/true_vals_letters', index=False)
        responses_letters_frame.to_csv(f'./exported_data/ID_{self.subj_ID}/responses_letters', index=False)
        true_vals_shapes_frame.to_csv(f'./exported_data/ID_{self.subj_ID}/true_vals_shapes', index=False)
        responses_shapes_frame.to_csv(f'./exported_data/ID_{self.subj_ID}/responses_shapes', index=False)
    

class RectangleCustom:
    def __init__(self, center, width, height, orientation=0.0, fill=True, color=(255.0, 255.0, 255.0)):
        """
        Initialize a Rectangle object.

        Parameters:
            center: Center coordinates of the rectangle as a tuple (x, y).
            width: Width of the rectangle.
            height: Height of the rectangle.
            orientation: Rotation angle of the rectangle in degrees.
            fill: If True, the rectangle will be filled. If False, only the outline will be drawn.
            color: RGB tuple (r, g, b) for the rectangle's color, with values between 0 and 255.
        """
        self.center = np.asarray(center, dtype=np.float32)
        self.width = float(width)
        self.height = float(height)
        self.orientation = float(orientation)
        self.fill = fill
        self.set_color(color)

    def set_center(self, center):
        self.center = np.asarray(center, dtype=np.float32)

    def set_size(self, width, height):
        self.width = float(width)
        self.height = float(height)

    def set_orientation(self, orientation):
        self.orientation = float(orientation)

    def set_color(self, color):
        self.color = np.asarray(color) / 255.0  # Normalize color to [0, 1]

    def draw(self):
        """
        Draw the rectangle using OpenGL.
        """
        glColor3f(*self.color)  # Set the rectangle's color

        # Choose the drawing mode
        if self.fill:
            glBegin(GL_QUADS)
        else:
            glBegin(GL_LINE_LOOP)

        # Calculate vertices of the rectangle
        w, h = self.width / 2, self.height / 2
        vertices = np.array([
            [-w, -h],
            [ w, -h],
            [ w,  h],
            [-w,  h],
        ], dtype=np.float32)

        # Rotate vertices based on the orientation
        angle_rad = np.radians(self.orientation)
        rotation_matrix = np.array([
            [np.cos(angle_rad), -np.sin(angle_rad)],
            [np.sin(angle_rad),  np.cos(angle_rad)]
        ], dtype=np.float32)
        rotated_vertices = np.dot(vertices, rotation_matrix.T)

        # Translate vertices to the center
        for vertex in rotated_vertices:
            glVertex2f(self.center[0] + vertex[0], self.center[1] + vertex[1])

        glEnd()


class EquilateralTriangle:
    def __init__(self, center, side_length, orientation=0.0, color=(255, 255, 255), fill=True):
        """
        Initialize an EquilateralTriangle object.

        Parameters:
            center: Center coordinates of the triangle as a tuple (x, y).
            side_length: Length of each side of the triangle.
            orientation: Rotation angle of the triangle in degrees.
            color: RGB tuple (r, g, b) for the triangle's color, with values between 0 and 255.
            fill: If True, the triangle will be filled. If False, only the outline will be drawn.
        """
        self.center = np.array(center, dtype=np.float32)
        self.side_length = float(side_length)
        self.orientation = float(orientation)
        self.set_color(color)
        self.fill = fill

    def set_color(self, color):
        self.color = np.array(color) / 255.0  # Normalize color to [0, 1]

    def draw(self):
        """
        Draw the equilateral triangle using OpenGL.
        """
        # Calculate the vertices of the triangle
        half_height = (np.sqrt(3) / 2) * self.side_length / 2
        vertices = np.array([
            [0, 2 * half_height],  # Top vertex
            [-self.side_length / 2, -half_height],  # Bottom-left vertex
            [self.side_length / 2, -half_height]   # Bottom-right vertex
        ])

        glPushMatrix()  # Save the current transformation matrix

        # Apply transformations
        glTranslatef(self.center[0], self.center[1], 0)
        glRotatef(self.orientation, 0, 0, 1)

        # Set the color
        glColor3f(*self.color)

        # Draw the triangle
        if self.fill:
            glBegin(GL_TRIANGLES)
        else:
            glBegin(GL_LINE_LOOP)
        
        for vertex in vertices:
            glVertex2f(vertex[0], vertex[1])
        glEnd()

        glPopMatrix()  # Restore the transformation matrix



def drawPracticeRectangle(space_pressed, stim_correct, CorrectRectangle):
    if space_pressed and stim_correct:
        CorrectRectangle.set_color([0,255,0])
        CorrectRectangle.draw()
    if space_pressed and not stim_correct:
        CorrectRectangle.set_color([255,0,0])
        CorrectRectangle.draw()


#some testing
# def makeNback2(elements, size, n, p):
#     '''
#     INPUT PARAMETERS
#     elements: any python list
#     size: length of the output list
#     n: value of the n-back task
#     p: proportion of stimuli which will be repeated in n-back fashion

#     OUTPUTS
#     result: list of length size containing
#             stimuli selected from elements and arranged according to n-back task
#     repeatLocs: list of length size. Equals 1 at locations where a repetition will occur
#     '''
#     numRepeats = round(p*size)

#     result = []
#     # Ensure that there are no unintended repetitions
#     for i in range(size):
#         available_elems = [elem for elem in elements if i < n or result[i - n] != elements]
#         if not available_elems:
#             raise ValueError("Not enough elements to satisfy the non-repeating condition.")
#         result.append(random.choice(available_elems))

#     result = np.zeros(size) - 1

#     #Randomly generate the locations which will have repeated elements
#     repeatLocs = np.zeros((size))
#     repeatLocsEnd = np.zeros((size))
#     repeatLocs[random.sample(range(size-n), numRepeats)] = 1
#     repeatLocsEnd[n:size] = repeatLocs[0:size-n]

#     result = np.array(result)

#     for i in range(size-n):
#         if repeatLocs[i] or repeatLocsEnd[i]: 
#             num = random.choice(elements)
#             result[i] = num

#     for i in range(size-n):
#         if repeatLocs[i]: 
#             result[i+n] = result[i]

#     for i in range(size):
#         if result[i] == -1:
#             allowed_numbers = [x for x in elements if (x != result[(i-n)%size] and x!= result[(i+n)%size])]
#             result[i] = random.choice(allowed_numbers)

#     result = [int(x) for x in result]
#     repeatLocsEnd = [int(x) for x in repeatLocsEnd]
#     return result, repeatLocsEnd

# a = range(9)
# n = 3
# p = 0.2
# size = 20

# result, locs = makeNback2(a, size, n, p)

# print(result)
# print(locs)