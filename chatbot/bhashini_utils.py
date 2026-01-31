import requests
import json
import base64

class BhashiniHandler:
    def __init__(self, user_id, api_key):
        self.user_id = user_id
        self.api_key = api_key
        # Pipeline ID for ASR, Translation, and TTS
        self.pipeline_id = "64392f96daac500b55c543cd"
        self.base_url = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"

    def _get_compute_config(self, task_type, source_lang, target_lang=None):
        """Retrieves dynamic callback URL and auth key for the specific task."""
        task_config = {"taskType": task_type, "config": {"language": {"sourceLanguage": source_lang}}}
        if target_lang:
            task_config["config"]["language"]["targetLanguage"] = target_lang

        payload = {
            "pipelineTasks": [task_config],
            "pipelineRequestConfig": {"pipelineId": self.pipeline_id}
        }
        headers = {"userID": self.user_id, "ulcaApiKey": self.api_key}
        
        response = requests.post(self.base_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        return (
            data["pipelineInferenceAPIEndPoint"]["callbackUrl"],
            data["pipelineInferenceAPIEndPoint"]["inferenceApiKey"]["value"],
            data["pipelineResponseConfig"][0]["config"][0]["serviceId"]
        )

    def speech_to_text(self, audio_base64, lang_code):
        """Converts user audio (base64) to text."""
        url, auth, service_id = self._get_compute_config("asr", lang_code)
        payload = {
            "pipelineTasks": [{"taskType": "asr", "config": {"language": {"sourceLanguage": lang_code}, "serviceId": service_id, "audioFormat": "wav"}}],
            "input": [{"audioContent": audio_base64}]
        }
        res = requests.post(url, json=payload, headers={"Authorization": auth})
        return res.json()["pipelineResponse"][0]["output"][0]["source"]

    def text_to_speech(self, text, lang_code):
        """Converts Gemini's response to local language audio."""
        url, auth, service_id = self._get_compute_config("tts", lang_code)
        payload = {
            "pipelineTasks": [{"taskType": "tts", "config": {"language": {"sourceLanguage": lang_code}, "serviceId": service_id}}],
            "input": [{"source": text}]
        }
        res = requests.post(url, json=payload, headers={"Authorization": auth})
        return res.json()["pipelineResponse"][0]["audio"][0]["audioContent"]