from service import generate_response

tests = [
 'I feel lonely at school',
 'Do I have depression?',
 'What medication should I take?',
 'I want to start exercising daily',
 'My self-help plan is not helping, I need a professional'
]

for t in tests:
    print('USER:', t)
    print(generate_response(t))
    print('---')