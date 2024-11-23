import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load dataset
data = pd.read_csv("data/data.csv")

# Recommend content based on user input
def recommend_content(age, content_type, skill_level):
    """
    Recommend content based on user input.
    """
    # Filter data based on content type and skill level
    filtered_data = data[
        (data["Content Type"] == content_type) &
        (data["Skill Level"] == skill_level)
    ]

    if filtered_data.empty:
        return []

    # Apply TF-IDF to the Recommended Content column
    vectorizer = TfidfVectorizer(stop_words="english")
    content_matrix = vectorizer.fit_transform(filtered_data["Recommended Content"])

    # Compute similarity between user input and available content
    user_input_vector = vectorizer.transform([f"{content_type} {skill_level}"])
    similarity_scores = cosine_similarity(user_input_vector, content_matrix)

    # Calculate age proximity and combined score
    filtered_data["age_proximity"] = 1 / (1 + abs(filtered_data["Age"] - age))
    filtered_data["combined_score"] = similarity_scores[0] + 0.5 * filtered_data["age_proximity"]

    # Sort the data by combined score and get the top 5 results
    filtered_data = filtered_data.sort_values(by="combined_score", ascending=False)
    recommendations = filtered_data.head(5)["Recommended Content"].tolist()

    return recommendations