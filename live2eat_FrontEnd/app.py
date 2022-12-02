import datetime
import glob
import os
import pickle
import statistics
import time
from datetime import timedelta
from typing import Optional, Sequence

import cv2
import numpy as np
import pandas as pd
import requests
import streamlit as st
from food_frame_export import *
from food_frame_extract import *
from food_prediction import *
from food_video_selection import *
from google.cloud import storage
from google.cloud import videointelligence as vi
from google.oauth2 import service_account
from sklearn.cluster import KMeans
from PIL import Image



# specify cloud credentials
#---------------------------------------------------------------
st.set_page_config(
    page_title="Live2Eat",
    page_icon="🐍",
    layout="centered",  # wide
    initial_sidebar_state="auto")  # collapsed



# page header
#---------------------------------------------------------------
'''
# Live2Eat Food Tracking
Take the hard work out of tracking your food

'''
st.markdown('#')




# video selection
#---------------------------------------------------------------
option = st.selectbox('Please select a video',
                      ('Video 1', 'Video 2', 'Video 3', 'Video 4', 'Video 5'))

if option == 'Video 1':  # Bak Chor Mee
    video_URL = 'https://www.youtube.com/watch?v=V4GR-TcqYkk'
if option == 'Video 3':  # Kaya Toast
    video_URL = 'https://www.youtube.com/watch?v=7R-iTYFaS6A'
if option == 'Video 2':  # Hokkien Mee
    video_URL = 'https://www.youtube.com/watch?v=3zH2Hw4EE_U'
if option == 'Video 4':  # Chilli Crab
    video_URL = 'https://www.youtube.com/watch?v=g--tLRttm18'
elif option == 'Video 5':  #Chicken Rice
    video_URL = 'https://www.youtube.com/watch?v=S3UJD08RrFQ'

st.video(video_URL, format="video/mp4", start_time=0)

st.markdown('#')
st.markdown('#')




# specify cloud credentials
#---------------------------------------------------------------
credentials = service_account.Credentials.from_service_account_info(
    st.secrets['gcp_service_account'])




# specify local folder locations
#---------------------------------------------------------------

dir = os.getcwd()
raw_data_dir = f'{dir}/raw_data'
export_path = f'{dir}/data/predict_images'

try:
    # creating a folder named data
    if not os.path.exists('raw_data'):
        os.makedirs('raw_data')

    if not os.path.exists('data'):
        os.makedirs('data/predict_images')

# if not created then raise error
except OSError:
    print('Error: Creating directory of data')




# select the video and download it
#---------------------------------------------------------------
video_uri = video_uri(option, credentials)
download_video_opencv(video_uri, credentials)

video_path = os.path.join(os.getcwd(), 'video.mp4')
print('Reading video from: ', video_path)
cam = cv2.VideoCapture(video_path)




# googleVideointelligence API video frames extract
#---------------------------------------------------------------

results = track_objects(video_uri, credentials)

with open("results.p", "wb") as f:
    pickle.dump(results, f)

with open("results.p", "rb") as f:
    results = pickle.load(f)

food_entity_id = '/m/02wbm'
food_times = print_object_frames(results, food_entity_id)
food_times = sorted(set(food_times))[::5]




# video frames export
#---------------------------------------------------------------

print('Current Dir: ', os.getcwd())
capture_images(food_times, cam, raw_data_dir)

sorted_dishes = sorted(glob.glob(raw_data_dir + "/*.jpg"),
                       key=lambda s: int(s.split('/')[-1].split('.')[0]))

print(f'length of {sorted_dishes = }')

print(f'length of sorted_dish after glob: {len(sorted_dishes)}')
dishes = create_dish_list(sorted_dishes)
resized_dishes = create_resized_dish_list(dishes)
resized_dishes_2d = create_reshaped_dish_list(resized_dishes)
file_labels = dish_clustering_dataframe(resized_dishes_2d, sorted_dishes)
median_dish(file_labels, raw_data_dir, export_path)




# model predict dishes
#---------------------------------------------------------------

prediction = predict()

prediction_df = pd.DataFrame({
    'dish name': [
        'BAK CHOR MEE', 'CHICKEN RICE', 'CHILLI CRAB', 'HOKKIEN MEE',
        'KAYA TOAST'
    ],
    'calories':['511 calories', '607 calories', '1560 calories', '617 calories', '196 calories'],
    'prediction': prediction[0]
})
prediction_df_sorted = prediction_df.sort_values(by='prediction', ascending=False)

st.markdown('#')


# display results
#---------------------------------------------------------------

dishes_predicted_names=prediction_df_sorted[0]
calories=prediction_df_sorted[2]
dish_images=prediction_df_sorted[1]


st.title("Dishes detected")

@st.cache(allow_output_mutation=True)

n = st.number_input("Grid Width", 1, 5, 2)

groups = []
for i in range(0, len(dish_images), n):
    groups.append(dish_images[i:i+n])
    groups.append(dishes_predicted_names[i:i+n])
    groups.append(calories[i:i+n])

for group in groups:
    cols = st.columns(n)
    for i, image, name in enumerate(group):
        image=Image.open(os.path.join(export_path, dish_file_name))
        cols[i].image(image)
        cols[i].text(name)
        cols[i].text(calories)


st.markdown('#')
st.markdown('#')




# log food selected
#---------------------------------------------------------------

if st.button('Submit'):
    st.success("Your choice has been submitted!")
