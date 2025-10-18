def generate_recommendations(answers):
    recommendations = set()
    if answers.get('q1') == 'My Family': recommendations.add('HEALTH'); recommendations.add('LIFE')
    elif answers.get('q1') == 'Myself': recommendations.add('HEALTH')
    if answers.get('q2') == 'Farmer': recommendations.add('CROP'); recommendations.add('LIVESTOCK')
    if answers.get('q2') == 'Business Owner': recommendations.add('PROPERTY')
    if answers.get('q4') == 'Yes': recommendations.add('VEHICLE')
    if not recommendations: recommendations.add('HEALTH')
    return list(recommendations)