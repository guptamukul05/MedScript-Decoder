with open('src/openfda_api.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("doctor's", "doctors")
content = content.replace("Traveler's", "Travelers")

with open('src/openfda_api.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed")