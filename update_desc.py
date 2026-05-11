import json

data = json.load(open('site/data.json', 'r', encoding='utf-8'))
for b in data:
    if b['title'] == 'Java_Core':
        b['description'] = 'Master the foundational elements of the Java programming language to build robust, scalable applications.\n\nThis comprehensive guide covers everything from basic syntax to object-oriented programming principles and advanced core features. It provides a solid grounding for developers looking to deepen their understanding of Java\'s core capabilities.\n\n• Learn object-oriented concepts like inheritance, encapsulation, and polymorphism.\n• Master exception handling and input/output operations.\n• Explore collections and generic programming to manage data efficiently.\n• Build concurrent applications using multi-threading techniques.'
    elif b['title'] == 'Java_Spring_Boot_Microservices_and_Angular':
        b['description'] = 'Navigate the complexities of building modern full-stack web applications using industry-standard tools.\n\nThis book guides you through integrating a Spring Boot backend with an Angular frontend, focusing on microservices architecture. It demonstrates how to combine these powerful frameworks to deliver responsive and scalable enterprise systems.\n\n• Master the creation of RESTful APIs with Java and Spring Boot.\n• Build dynamic single-page applications using Angular.\n• Implement microservices patterns for decoupled backend architecture.\n• Deploy and manage full-stack applications effectively.'

with open('site/data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print('Updated descriptions in data.json')
