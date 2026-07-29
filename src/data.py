IRRELEVANT_TOPICS = [
    "Sourdough bread baking requires maintaining a starter with equal parts flour and water daily.",
    "Ancient Rome spanned over a thousand years from 753 BCE to the fall of the Western Empire in 476 CE.",
    "Kubernetes is a container orchestration platform for automating deployment, scaling, and management.",
    "Photosynthesis converts sunlight into chemical energy in green plants, producing oxygen as a byproduct.",
    "The FIFA World Cup is held every four years; Brazil holds the record with five championship titles.",
    "Machine learning enables systems to learn patterns from data without being explicitly programmed.",
    "The Great Wall of China stretches over 13,000 miles across northern China's historical borders.",
    "JavaScript is a programming language primarily used for web development on both frontend and backend.",
    "The human body contains approximately 37.2 trillion cells, each performing specialized functions.",
    "React is a JavaScript library for building user interfaces, maintained by Meta.",
    "The Pythagorean theorem states that a^2 + b^2 = c^2 for right-angled triangles.",
    "Coffee originated in Ethiopia and is one of the most widely consumed beverages worldwide.",
    "Docker provides lightweight operating-system-level virtualization; images are built from Dockerfiles.",
    "The Amazon rainforest produces roughly 20 percent of the world's oxygen supply.",
    "Cricket is a bat-and-ball sport popular in the UK, India, Australia, and other Commonwealth nations.",
    "Rust is a systems programming language focused on safety, speed, and concurrency.",
    "The Eiffel Tower in Paris was completed in 1889 and stands 330 meters tall.",
    "Yoga originated in ancient India and includes physical postures, breathing techniques, and meditation.",
    "The stock market allows investors to buy and sell shares of publicly traded companies.",
    "Shakespeare wrote 37 plays and 154 sonnets during his literary career.",
    "Mars is the fourth planet from the Sun, often called the Red Planet due to its iron oxide surface.",
    "TypeScript adds static type definitions to JavaScript, improving developer experience and code quality.",
    "The Fibonacci sequence starts with 0 and 1; each subsequent number is the sum of the two preceding ones.",
    "The Mediterranean diet emphasizes fruits, vegetables, whole grains, and healthy fats like olive oil.",
    "Blockchain is a distributed ledger technology that underpins cryptocurrencies such as Bitcoin.",
    "The average adult human brain weighs approximately 1.3 to 1.4 kilograms.",
    "Beethoven composed 9 symphonies, with the Fifth being one of the most recognizable in classical music.",
    "The Sahara Desert is the largest hot desert in the world, covering most of North Africa.",
    "HTTP is the foundation of data communication on the World Wide Web, defining request-response protocols.",
    "The Mona Lisa was painted by Leonardo da Vinci in the early 16th century and resides in the Louvre.",
]


def generate_dataset() -> dict:
    candidate = {
        "name": "Alex Chen",
        "years_experience": 1.5,
        "skills": [
            "Python", "Django", "SQL", "Git",
            "REST APIs", "PostgreSQL", "Linux", "HTML", "CSS",
        ],
        "education": "B.S. Computer Science, University of California, 2024",
        "projects": [
            {
                "name": "Task Manager API",
                "description": (
                    "RESTful task management API built with Django REST Framework, "
                    "PostgreSQL, and JWT authentication. Supports CRUD, filtering, pagination."
                ),
            },
            {
                "name": "Blog Platform",
                "description": (
                    "Blog platform with Django, user authentication, comments, "
                    "Markdown support, and PostgreSQL database."
                ),
            },
        ],
    }

    job = {
        "title": "Junior Python Backend Developer",
        "required_skills": ["Python", "Django", "SQL", "REST APIs"],
        "nice_to_have": ["Docker", "AWS", "Redis", "Celery"],
        "description": (
            "Looking for a junior Python backend developer to build and maintain "
            "REST APIs, work with PostgreSQL, and collaborate on Django-based services."
        ),
    }

    query = (
        f"Evaluate {candidate['name']} for {job['title']}. "
        f"Experience: {candidate['years_experience']} years. "
        f"Skills: {', '.join(candidate['skills'])}."
    )

    relevant_documents = [
        (
            "Project - Task Manager API: RESTful task management API built with "
            "Django REST Framework, PostgreSQL, and JWT authentication. "
            "Supports CRUD operations, filtering, and pagination."
        ),
        (
            "Project - Blog Platform: Blog platform built with Django, user "
            "authentication, comments section, Markdown support, and PostgreSQL."
        ),
        (
            "Python is a high-level, interpreted programming language known for "
            "readability. Widely used in web development, data science, and automation."
        ),
        (
            "Django is a high-level Python web framework that encourages rapid "
            "development. Includes ORM, authentication, admin interface, and URL routing."
        ),
        (
            "REST APIs are an architectural style for networked applications. "
            "HTTP methods (GET, POST, PUT, DELETE) map to standard CRUD operations."
        ),
    ]

    irrelevant_documents = list(IRRELEVANT_TOPICS)

    return {
        "candidate": candidate,
        "job": job,
        "query": query,
        "relevant_documents": relevant_documents,
        "irrelevant_documents": irrelevant_documents,
        "all_documents": relevant_documents + irrelevant_documents,
    }