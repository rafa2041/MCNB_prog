'''
NOTE: this code is based on and extends the code from tachypy_example3.py.
'''
import time
from tachypy import (
    Text,
    Screen,
    FixationCross,
    center_rect_on_point,
    ResponseHandler,
    Rectangle,
)

### INITIALIZE THE EXPERIMENT 
#Choose subject ID, list of n-back levels, number of rounds per level, and proportion of stimuli which are repeats
from generator import *
exp = Exp(subj_ID = 1, n_list = [1,2], num_rounds = 10, proportion_repeats = 0.22, 
    im_h=300, im_w=300, stim_interval=2, stim_duration=0.5)
practice = 1

#Note: We compensate for algorithm by using p = 0.22 instead of 0.2

### CONVERT S TO NS FOR TIMING
stim_interval_ns = exp.stim_interval*1e9
stim_duration_ns = exp.stim_duration*1e9

### SETUP STUFF THAT WE'LL USE FOR ALL SCRIPTS
# Define screen we will draw to
screen_number = 1
screen = Screen(screen_number=screen_number, fullscreen=False, desired_refresh_rate=60)

# flip the screen (needed for frame_rate measruement below)
screen.fill([128, 128, 128])
# flip the screen to make the background color visible
screen.flip()

# get some relevant screen properties
center_x = screen.width//2
center_y = screen.height//2
frame_rate_measured = 1/screen.test_flip_intervals(num_frames=100)
half_ifi_s = 1/(2*frame_rate_measured)  # half the inter-frame interval in seconds
half_ifi_ns = half_ifi_s*1e9  # half the inter-frame interval in nanoseconds
print(f'Measured frame rate: {frame_rate_measured:.2f} Hz')

rectangle = RectangleCustom([center_x, center_y], 400, 200)
square = RectangleCustom([center_x, center_y], 250, 250)
triangle = EquilateralTriangle([center_x, center_y], 300, orientation = 180)

shape_list = [rectangle, square, triangle]

CorrectRectangle = RectangleCustom([center_x, center_y-300], 100, 100)


### LOAD UP STUFF WE WANT TO SHOW ON SCREEN
fixation_cross = FixationCross(center=[center_x, center_y], half_width=10, half_height=10, thickness=5.0, color=(0, 0, 0))

# define the position in which the Texture will be mapped.
dest_rect = center_rect_on_point([0, 0, exp.im_w-1, exp.im_h-1], [center_x, center_y])

### INITIALIZE RESPONSE HANDLER
response_handler = ResponseHandler(keys_to_listen=['escape', 'space'])

# flip an initial screen and record starting time
screen.fill([128, 128, 128])
start_time = screen.flip() # returns time in ns
#exp.logs_timing['start'] = start_time/1e9 # ns to s


### PRESENT WELCOME TEXT AND WAIT FOR RESPONSE TO START
# print welcome message
screen.fill([128, 128, 128])
welcome_message = Text('Welcome to the experiment! Press the space bar to proceed, escape to quit', dest_rect=dest_rect, font_name='Helvetica', font_size=24, color=(0, 0, 0))
welcome_message.draw()
screen.flip()
while True:
    response_handler.get_events()
    if response_handler.is_key_down('space'):
        break

variation_list = ['letter', 'shape']
if(exp.subj_ID%2==0): variation_list = ['shape', 'letter']
exp.fullData['variation_list'] = variation_list

exp.save_expt()

# ### LOOP OVER TRIALS
for variation in variation_list: #Loop over letters and shapes

    for j in range(len(exp.n_list)): #Loop over n = 1,2,3
        n = exp.n_list[j]
        shape_message = Text(f'Shapes will be presented one at a time. Take note of them. If the shape on the screen is the same type and color as the one seen {n} letters before, press the spacebar. Press the spacebar to proceed.', dest_rect=dest_rect, font_name='Helvetica', font_size=24, color=(0, 0, 0))
        letter_message = Text(f'Letters will be presented one at a time. Take note of them. If the letter on the screen is the same as the one seen {n} letters before, press the spacebar. The case of the letter does not matter. Press the spacebar to proceed.', dest_rect=dest_rect, font_name='Helvetica', font_size=24, color=(0, 0, 0))
        if(variation == 'letter'): message = letter_message
        if(variation == 'shape'): message = shape_message
        screen.fill([128, 128, 128])
        message.draw()
        screen.flip()
        while True:
            response_handler.get_events()
            if response_handler.is_key_down('space'):
                break

        trial_start_ns = time.monotonic_ns() # get the current time in nanoseconds

        # fixation cross
        estimated_time = trial_start_ns + stim_interval_ns
        while time.monotonic_ns() < estimated_time - half_ifi_ns:
            screen.fill([128, 128, 128])
            fixation_cross.draw()
            true_time = screen.flip()

        exp.generate_trials(n)

        exp.fullData[f'true_vals_{variation}s'][j,:] = exp.stim_locs

        for round in range(exp.num_rounds): #Gp through 50 stimuli presentations

            space_pressed = 0
            # stimulus presentation
            if(variation == 'letter'):
                letter = exp.letters_list[exp.stim_indeces[round]]
                if((int)(random.randrange(0, 2)) & 1): letter = letter.lower()
                display = Text(letter, dest_rect=dest_rect, font_name='Helvetica', font_size=100, color=(0, 0, 0))
            else:
                shape = exp.shapes_colors_list[exp.stim_indeces[round]][0]
                color = exp.shapes_colors_list[exp.stim_indeces[round]][1]
                display = shape_list[shape]
                display.set_color(color)

            estimated_time = estimated_time + stim_duration_ns
            while time.monotonic_ns() < estimated_time - half_ifi_ns:
                screen.fill([128, 128, 128])
                display.draw()
                if practice: drawPracticeRectangle(space_pressed, exp.stim_locs[round], CorrectRectangle)

                true_time = screen.flip()

                response_handler.get_events()
                if response_handler.is_key_down('space') and not space_pressed:
                    space_pressed = 1


            #inter-stimulus interval
            estimated_time = estimated_time + stim_interval_ns
            while time.monotonic_ns() < estimated_time - half_ifi_ns:
                screen.fill([128, 128, 128])
                fixation_cross.draw()
                if practice: drawPracticeRectangle(space_pressed, exp.stim_locs[round], CorrectRectangle)
                
                response_handler.get_events()
                if response_handler.is_key_down('space') and not space_pressed:
                    space_pressed = 1

                true_time = screen.flip()

            exp.fullData[f'responses_{variation}s'][j,round] = space_pressed
                
            
screen.fill([128, 128, 128])
goodbye_message = Text('Experiment finished! Press the space bar to quit', dest_rect=dest_rect, font_name='Helvetica', font_size=24, color=(0, 0, 0))
goodbye_message.draw()
screen.flip()
while True:
    response_handler.get_events()
    if response_handler.is_key_down('space'):
        break 
            




# for trial in num_trials
#     # # create empty "subdicts" for this trial (only needed for dicts, not for pandas)
#     # exp.logs_timing[f'trial_{trial}'] = {}

#     # # log the start of the trial and start trial timer
#     trial_start_ns = time.monotonic_ns() # get the current time in nanoseconds
#     # exp.logs_timing[f'trial_{trial}']['trialStart'] = trial_start_ns/1e9  # log in seconds

#     # # look into our trial list to get the categ and image id
#     # trial_categ = exp.trial_info.loc[trial, 'categ']
#     # trial_categ_id = exp.trial_info.loc[trial, 'categ_id']
#     # trial_img = exp.trial_info.loc[trial, 'img_id']
#     # # get the corresponding texture
#     # trial_texture = all_textures[trial_categ][trial_img]
        

#     # pre-stimulus blank screen presented for trial_start_interval_ns nanoseconds
#     estimated_time = trial_start_ns + stim_interval_ns
#     while time.monotonic_ns() < estimated_time - half_ifi_ns:
#         screen.fill([128, 128, 128])
#         fixation_cross.draw()
#         true_time = screen.flip()
#     exp.logs_timing[f'trial_{trial}']['stimOnset'] = {'estimated': (estimated_time-trial_start_ns)/1e9, 
#                                                       'true': (true_time-trial_start_ns)/1e9} # ns to s
#     # stimulus presentation
#     estimated_time = estimated_time + stim_duration_ns
#     while time.monotonic_ns() < estimated_time - half_ifi_ns:
#         screen.fill([128, 128, 128])
#         trial_texture.draw(dest_rect)
#         fixation_cross.draw()
#         true_time = screen.flip()
#     exp.logs_timing[f'trial_{trial}']['stimOffset'] = {'estimated': (estimated_time-trial_start_ns)/1e9, 
#                                                        'true': (true_time-trial_start_ns)/1e9} # ns to s


#     # get response
#     screen.fill([128, 128, 128])
#     instruction = Text('Press left arrow for cameleon, right for goat', dest_rect=dest_rect, font_name='Helvetica', font_size=24, color=(0, 0, 0))
#     instruction.draw()
#     response_start_time = screen.flip()
#     response_handler.get_events() # get rid of any lingering key presses
#     while True:
#         response_handler.get_events()
#         if response_handler.is_key_down('left'):
#             response = 0
#             break
#         elif response_handler.is_key_down('right'):
#             response = 1
#             break
#         elif response_handler.is_key_down('escape'):
#             screen.close()
#             exit()
#     response_given_time = time.monotonic_ns()
#     exp.trial_responses.loc[trial, 'response'] = response
#     exp.trial_responses.loc[trial, 'RT'] = (response_given_time - response_start_time)/1e9  # ns to s
#     correct = response == trial_categ_id
#     exp.trial_responses.loc[trial, 'accuracy'] = correct
    
#     # wait with sloppy timing as this is not critical
#     time.sleep(0.5)

#     # Display feedback text
#     screen.fill([128, 128, 128])
#     text_str = 'Correct!' if correct else 'Incorrect.'
#     feedback_message = Text(text_str, dest_rect=dest_rect, font_name='Helvetica', font_size=24, color=(0, 0, 0))
#     feedback_message.draw()
#     screen.flip()

#     # wait with sloppy timing as this is not critical
#     time.sleep(0.5)

# # print goodbye message
# screen.fill([128, 128, 128])
# goodbye_message = Text('Goodbye!', dest_rect=dest_rect, font_name='Helvetica', font_size=24, color=(0, 0, 0))
# goodbye_message.draw()
# screen.flip()

#  # wait with sloppy timing as this is not critical
# time.sleep(2)

# # close the screen
# screen.close()

# # save everything (responses, timing_logs, and Exp instance)

exp.save_expt()
print('Experiment finished!')
