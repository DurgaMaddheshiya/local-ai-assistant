"""
Tests for settings API
"""


class TestGetSettings:

    def test_get_settings_returns_200(self, client):
        response = client.get("/api/settings")
        assert response.status_code == 200

    def test_get_settings_has_required_fields(self, client):
        response = client.get("/api/settings")
        data = response.json()
        assert "current_model" in data
        assert "temperature" in data
        assert "max_tokens" in data
        assert "system_prompt" in data

    def test_temperature_is_float(self, client):
        response = client.get("/api/settings")
        data = response.json()
        assert isinstance(data["temperature"], float)

    def test_max_tokens_is_int(self, client):
        response = client.get("/api/settings")
        data = response.json()
        assert isinstance(data["max_tokens"], int)
        assert data["max_tokens"] > 0

    def test_system_prompt_is_non_empty_string(self, client):
        response = client.get("/api/settings")
        data = response.json()
        assert isinstance(data["system_prompt"], str)
        assert len(data["system_prompt"]) > 0


class TestUpdateSettings:

    def test_update_temperature(self, client):
        response = client.patch("/api/settings", json={"temperature": 0.5})
        assert response.status_code == 200
        data = response.json()
        assert data["settings"]["temperature"] == 0.5

    def test_update_max_tokens(self, client):
        response = client.patch("/api/settings", json={"max_tokens": 1024})
        assert response.status_code == 200
        data = response.json()
        assert data["settings"]["max_tokens"] == 1024

    def test_update_system_prompt(self, client):
        new_prompt = "You are a custom assistant."
        response = client.patch("/api/settings", json={"system_prompt": new_prompt})
        assert response.status_code == 200
        data = response.json()
        assert data["settings"]["system_prompt"] == new_prompt

    def test_update_invalid_temperature_rejected(self, client):
        # Temperature must be 0.0–2.0
        response = client.patch("/api/settings", json={"temperature": 5.0})
        assert response.status_code == 422

    def test_update_negative_max_tokens_rejected(self, client):
        response = client.patch("/api/settings", json={"max_tokens": -1})
        assert response.status_code == 422

    def test_partial_update_only_changes_specified_fields(self, client):
        # Record baseline
        baseline = client.get("/api/settings").json()

        # Only update temperature
        client.patch("/api/settings", json={"temperature": 1.0})

        # Max tokens should be unchanged
        after = client.get("/api/settings").json()
        assert after["max_tokens"] == baseline["max_tokens"]

    def test_update_returns_updated_fields_list(self, client):
        response = client.patch("/api/settings", json={"temperature": 0.9})
        data = response.json()
        assert "updated_fields" in data
        assert "temperature" in data["updated_fields"]


class TestTheme:

    def test_set_light_theme(self, client):
        response = client.post("/api/settings/theme?theme=light")
        assert response.status_code == 200
        assert response.json()["theme"] == "light"

    def test_set_dark_theme(self, client):
        response = client.post("/api/settings/theme?theme=dark")
        assert response.status_code == 200
        assert response.json()["theme"] == "dark"

    def test_set_invalid_theme_rejected(self, client):
        response = client.post("/api/settings/theme?theme=rainbow")
        assert response.status_code == 400

    def test_get_theme(self, client):
        # Set first, then get
        client.post("/api/settings/theme?theme=dark")
        response = client.get("/api/settings/theme")
        assert response.status_code == 200
        assert response.json()["theme"] == "dark"
