import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import pickle

data = pd.read_csv('cleaned_merged_dataset.csv')

# Combine symptoms into a single text column
data['combined_symptoms'] = data[['Symptom 1', 'Symptom 2', 'Symptom 3']].apply(lambda x: ' '.join(x), axis=1)

# Encode the 'Disease' column as the target
label_encoder = LabelEncoder()
data['Disease_encoded'] = label_encoder.fit_transform(data['Disease'])

# Split the data into features and target
X = data[['Animal','Age', 'Temperature', 'combined_symptoms']]
y = data['Disease_encoded']

# Split into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Build a pipeline that vectorizes the symptoms and applies a Random Forest classifier
pipeline = make_pipeline(
    TfidfVectorizer(),
    RandomForestClassifier(n_estimators=100, random_state=42)
)

# Train the model
pipeline.fit(X_train['combined_symptoms'], y_train)

# Save the trained model and label encoder using pickle
with open('disease_prediction_model.pkl', 'wb') as model_file:
    pickle.dump(pipeline, model_file)

with open('label_encoder.pkl', 'wb') as encoder_file:
    pickle.dump(label_encoder, encoder_file)

# Optional: Test the model on the test set
y_pred = pipeline.predict(X_test['combined_symptoms'])
accuracy = (y_pred == y_test).mean()
print(f"Model Accuracy: {accuracy * 100:.2f}%")