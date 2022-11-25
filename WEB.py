import streamlit as st
import pandas as pd
from sklearn import datasets
from sklearn.ensemble import RandomForestClassifier
st.sidebar.header('User Input Parameters')
def user_input_features():
    # значения ввода
    data = { }
    features = pd.DataFrame(data, index=[0])
    return features
df = user_input_features()
iris = datasets.load_iris()
X = iris.data
