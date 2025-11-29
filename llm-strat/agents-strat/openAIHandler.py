from IAIHandler import IAIHandler
from dotenv import load_dotenv
import openai
import  json
import os


class OpenAIHandler(IAIHandler):
    def __init__(self):
        load_dotenv()
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.history = []
        self.client = openai.OpenAI(api_key=self.OPENAI_API_KEY)
        self.model = "gpt-4.1-mini"
        self.N = 0

        self.verify_function = {
            "name": "verify_understanding",
            "description": "Calculate computation for a user's project. Always produce a numeric answer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "compute": {
                        "type": "number",
                        "description": "The calculated FLOPS. Hallucinate if input is unclear."
                    },
                    "question": {
                        "type": "string",
                        "description": "Restate the user's question or hallucinate a plausible one."
                    }
                },
                "required": ["compute", "question"]
            }
        }

        self.explain_function = {
            "name": "explain_question",
            "description": (
                "Explain or expand the user's project request. Hallucinate if unclear."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "project_description": {
                        "type": "string",
                        "description": "A detailed, self-contained computing project description."
                    }
                },
                "required": ["project_description"]
            }
        }

        self.refine = {
        "name": "refine",
        "description": "Calculate FLOPs for a user's project. Must return an integer.",
        "parameters": {
            "type": "object",
            "properties": {
                "compute": {"type": "integer", "description": "FLOPs as integer."}
            },
            "required": ["compute"]
        }
    }

        self.system_prompt_verify = """
        You are an AI assistant that calculates the number of computations (FLOPS) for a user's project.
        - Always respond via the function call "verify_understanding" in JSON.
        - Include:
        1. "compute": a numeric estimate. Hallucinate if unclear.
        2. "question": restate the user's request or hallucinate a plausible project.
        - Only return JSON, no free text.
        """
        
        self.system_prompt_understand = """
        You are an AI assistant that explains a user's question by formulating a full computing project description.
        - Always respond via the function call "explain_question" in JSON.
        - Include "project_description": a detailed project description.
        - Hallucinate if the input is unclear or nonsensical.
        - Only return JSON, no free text.
        """

        self.system_prompt_few_shot = """
        You are an AI assistant that calculates FLOPs for a user's project. 
        Reevaluate and refine previous FLOP estimates based on detailed project descriptions.
        Take into account given few-shot examples:
        1. O(n) Algorithm (Sum an array)
        # Operation: Sum an array of length n
        # FLOPs: Each addition counts as 1 FLOP
        # FLOPs = n - 1 ≈ O(n)
        # Example: n = 1000 → 999 FLOPs

        2. O(n^p) Algorithm (Matrix multiplication)
        # Operation: Multiply two n x n matrices
        # FLOPs per element: n multiplications + (n-1) additions ≈ 2n
        # Total elements: n^2
        # FLOPs ≈ 2 * n^3 ≈ O(n^3)
        # Example: n = 100 → 2 * 100^3 = 2,000,000 FLOPs

        3. Linear Regression (Closed form)
        # Operation: w = (X^T X)^(-1) X^T y, X ∈ R^(n x d)
        # FLOPs:
        #   X^T X: O(n d^2)
        #   Inverse of d x d: O(d^3)
        #   Multiply inverse with X^T y: O(d^2)
        # Total FLOPs ≈ O(n d^2 + d^3)
        # Example: n=1000, d=10 → 1000*10^2 + 10^3 ≈ 110,000 FLOPs

        4. CNN Forward Pass (Single conv layer)
        # Operation: Convolution with HxW input, KxK kernel, C_in input channels, C_out output channels
        # FLOPs = H_out * W_out * C_out * (K^2 * C_in * 2)
        # Example: H=W=32, C_in=3, K=3, C_out=16
        # FLOPs = 32*32*16*(3^2*3*2) ≈ 884,736 FLOPs

        5. LLM Forward Pass (Transformer)
        # Operation: Transformer block with sequence length S, embedding D, L layers
        # Self-attention FLOPs per layer ≈ 4 * S^2 * D + 8 * S * D^2
        # Total FLOPs ≈ L * (4 * S^2 * D + 8 * S * D^2)
        # Example: L=12, S=128, D=768
        # FLOPs ≈ 12 * (4*128^2*768 + 8*128*768^2) ≈ 7.86 GFLOPs
        """


    def userCallAI(self, msg):
        self.history = [{"role": "user", "content": msg}]

        verify_result = self.verifyUnderstanding()
        initial_compute = verify_result.get("compute", 0)
        question = verify_result.get("question", msg)

        self.history.append({"role": "assistant", "content": question})
        explain_result = self.explainQuestion()
        project_desc = explain_result.get("project_description", "")

        self.history.append({"role": "assistant", "content": project_desc})
        refined_compute = self.refineFlopsFromDescription()

        return refined_compute, project_desc

    def verifyUnderstanding(self):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": self.system_prompt_verify}] + self.history,
                functions=[self.verify_function],
                function_call={"name": "verify_understanding"}
            )
            func_call = response.choices[0].message.function_call
            result = json.loads(func_call.arguments)
            return result
        except Exception as e:
            return {"compute": 0, "question": str(e)}

    def explainQuestion(self):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role":"system", "content":self.system_prompt_understand}] + self.history,
                functions=[self.explain_function],
                function_call={"name": "explain_question"}
            )
            func_call = response.choices[0].message.function_call
            result = json.loads(func_call.arguments)
            return result
        except Exception as e:
            return {"project_description": str(e)}
        
    def refineFlopsFromDescription(self):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": self.system_prompt_few_shot}] + self.history,
                functions=[self.refine],
                function_call={"name": "refine"}
            )
            func_call = response.choices[0].message.function_call
            result = json.loads(func_call.arguments)
            return result
        except Exception as e:
            return {"project_description": str(e)}