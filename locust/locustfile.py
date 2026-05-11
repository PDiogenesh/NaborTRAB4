from locust import HttpUser, task, constant

class LinkExtractorUser(HttpUser):
    # Sem espera entre requisições — carga máxima
    wait_time = constant(0)

    # 10 URLs fixas, executadas em sequência por cada usuário virtual
    urls = [
        "https://en.wikipedia.org/wiki/Docker_(software)",
        "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "https://en.wikipedia.org/wiki/Ruby_(programming_language)",
        "https://en.wikipedia.org/wiki/PHP",
        "https://en.wikipedia.org/wiki/Redis",
        "https://en.wikipedia.org/wiki/Microservices",
        "https://en.wikipedia.org/wiki/Representational_state_transfer",
        "https://en.wikipedia.org/wiki/Load_testing",
        "https://en.wikipedia.org/wiki/Software_performance_testing",
        "https://en.wikipedia.org/wiki/Scalability",
    ]

    @task
    def extract_links(self):
        """Cada VU executa exatamente as 10 URLs em sequência."""
        for url in self.urls:
            self.client.get(f"/?url={url}", name="Extract Links")
