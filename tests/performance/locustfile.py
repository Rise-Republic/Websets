from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def root(self):
        self.client.get('/')
