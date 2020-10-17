import asyncio
import pandas as pd
import numpy as np

# Preprocessing
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler


event_loop = asyncio.get_event_loop()


async def build_dataset(dataset=None, test_size=None):
    if dataset is None or test_size is None:
        return (None, None)
    try:
        data = pd.DataFrame(dataset)
        # Dropping unneccesary columns
        data = data.drop(['filename'],axis=1)
        # Encoding the Labels
        genre_list = data.iloc[:, -1]
        encoder = LabelEncoder()
        y = encoder.fit_transform(genre_list)
        # Scaling the Feature columns
        scaler = StandardScaler()
        X = scaler.fit_transform(np.array(data.iloc[:, :-1], dtype = float))
        # Dividing data into training and Testing set
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size)
        return (True, {
            'X_train': X_train,
            'X_test': X_test,
            'y_train': y_train,
            'y_test': y_test
        })
    except Exception as ex:
        return (False , ex)
    return (None, None)

