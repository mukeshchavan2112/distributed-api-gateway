
from locust import HttpUser, between, task


class GatewayUser(HttpUser):
    # Wait between 1 and 2 seconds between requests from each simulated user.
    wait_time = between(1, 2)

    @task
    def request_hello(self):
        with self.client.get(
            "/api/hello",
            name="/api/hello",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"Unexpected status code: {response.status_code}"
                )
                return

            try:
                data = response.json()
            except ValueError:
                response.failure("Response was not valid JSON")
                return

            if data.get("backend") not in {"backend-a", "backend-b"}:
                response.failure("Unexpected backend response")
